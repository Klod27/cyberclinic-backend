import os
import stripe
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
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

# ----------------------------------
# SECURITY
# ----------------------------------
security = HTTPBearer()

# ----------------------------------
# ROUTER
# ----------------------------------
router = APIRouter()


# ----------------------------------
# CREATE CHECKOUT SESSION
# ----------------------------------
@router.post("/billing/create-checkout-session")
def create_checkout_session(
    mode: str = "report",
    report_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    credentials = Depends(security)
):

    if not stripe.api_key:
        raise HTTPException(500, "Stripe not configured")

    try:
        # ----------------------------------
        # CREATE CUSTOMER
        # ----------------------------------
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "organization_id": str(current_user.organization_id)
            }
        )

        # ----------------------------------
        # SUBSCRIPTION
        # ----------------------------------
        if mode == "subscription":

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="subscription",
                customer=customer.id,
                line_items=[{
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1
                }],
                success_url="http://localhost:3000",
                cancel_url="http://localhost:3000",
                metadata={
                    "user_id": str(current_user.id),
                    "organization_id": str(current_user.organization_id),
                    "type": "subscription"
                }
            )

        # ----------------------------------
        # REPORT PAYMENT
        # ----------------------------------
        else:

            if not report_id:
                raise HTTPException(400, "report_id is required")

            report = db.query(Report).filter(
                Report.id == report_id
            ).first()

            if not report:
                raise HTTPException(404, "Report not found")

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                customer=customer.id,
                line_items=[{
                    "price": STRIPE_REPORT_PRICE,
                    "quantity": 1
                }],
                success_url="http://localhost:3000",
                cancel_url="http://localhost:3000",
                metadata={
                    "report_id": str(report.id),
                    "user_id": str(current_user.id),
                    "organization_id": str(current_user.organization_id),
                    "type": "report"
                }
            )

            # Save session ID for tracking
            report.stripe_session_id = session.id
            db.commit()

        return {"url": session.url}

    except Exception as e:
        print("❌ Stripe Error:", str(e))
        raise HTTPException(500, str(e))