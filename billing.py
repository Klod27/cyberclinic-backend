import os
from pathlib import Path

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import User, Report

# ----------------------------------
# LOAD ENV
# ----------------------------------
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ----------------------------------
# STRIPE CONFIG
# ----------------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
STRIPE_REPORT_PRICE = os.getenv("STRIPE_REPORT_PRICE")

FRONTEND_URL = (
    os.getenv("FRONTEND_URL")
    or os.getenv("CLIENT_URL")
    or "https://cyberclinicsaas.com"
)

# ----------------------------------
# ROUTER
# ----------------------------------
router = APIRouter()


@router.post("/billing/create-checkout-session")
def create_checkout_session(
    mode: str = "subscription",
    report_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe secret key is not configured.")

    if mode == "subscription" and not STRIPE_PRICE_ID:
        raise HTTPException(status_code=500, detail="Stripe subscription price ID is not configured.")

    if mode == "report" and not STRIPE_REPORT_PRICE:
        raise HTTPException(status_code=500, detail="Stripe report price ID is not configured.")

    try:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "organization_id": str(getattr(current_user, "organization_id", "default")),
            },
        )

        if mode == "subscription":
            session = stripe.checkout.Session.create(
                mode="subscription",
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": STRIPE_PRICE_ID,
                        "quantity": 1,
                    }
                ],
                success_url=f"{FRONTEND_URL}/dashboard?checkout=success",
                cancel_url=f"{FRONTEND_URL}/pricing?checkout=cancelled",
                metadata={
                    "user_id": str(current_user.id),
                    "organization_id": str(getattr(current_user, "organization_id", "default")),
                    "type": "subscription",
                },
            )

            return {"url": session.url, "session_id": session.id}

        if mode == "report":
            if not report_id:
                raise HTTPException(status_code=400, detail="report_id is required for report checkout.")

            report = db.query(Report).filter(Report.id == report_id).first()

            if not report:
                raise HTTPException(status_code=404, detail="Report not found.")

            session = stripe.checkout.Session.create(
                mode="payment",
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": STRIPE_REPORT_PRICE,
                        "quantity": 1,
                    }
                ],
                success_url=f"{FRONTEND_URL}/dashboard?report=success",
                cancel_url=f"{FRONTEND_URL}/pricing?report=cancelled",
                metadata={
                    "report_id": str(report.id),
                    "user_id": str(current_user.id),
                    "organization_id": str(getattr(current_user, "organization_id", "default")),
                    "type": "report",
                },
            )

            report.stripe_session_id = session.id
            db.commit()

            return {"url": session.url, "session_id": session.id}

        raise HTTPException(status_code=400, detail="Invalid checkout mode.")

    except HTTPException:
        raise

    except Exception as e:
        print("❌ Stripe Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))