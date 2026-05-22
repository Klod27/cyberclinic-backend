import os
from pathlib import Path

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import User, Report

# ==================================
# LOAD ENV
# ==================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

# ==================================
# STRIPE CONFIG
# ==================================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
STRIPE_REPORT_PRICE = os.getenv("STRIPE_REPORT_PRICE")

FRONTEND_URL = (
    os.getenv("FRONTEND_URL")
    or os.getenv("CLIENT_URL")
    or "https://cyberclinicsaas.com"
)

# ==================================
# ROUTER
# ==================================

router = APIRouter()

# ==================================
# CREATE STRIPE CHECKOUT SESSION
# ==================================

@router.post("/billing/create-checkout-session")
def create_checkout_session(
    mode: str = "subscription",
    report_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # ==================================
    # VALIDATION
    # ==================================

    if not stripe.api_key:
        raise HTTPException(
            status_code=500,
            detail="Stripe secret key missing."
        )

    if mode == "subscription" and not STRIPE_PRICE_ID:
        raise HTTPException(
            status_code=500,
            detail="Missing STRIPE_PRICE_ID"
        )

    if mode == "report" and not STRIPE_REPORT_PRICE:
        raise HTTPException(
            status_code=500,
            detail="Missing STRIPE_REPORT_PRICE"
        )

    try:

        # ==================================
        # CREATE / REUSE STRIPE CUSTOMER
        # ==================================

        customer_id = current_user.stripe_customer_id

        if not customer_id:

            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={
                    "user_id": str(current_user.id),
                    "organization_id": str(current_user.organization_id),
                }
            )

            customer_id = customer.id

            current_user.stripe_customer_id = customer_id
            db.commit()

        # ==================================
        # SUBSCRIPTION CHECKOUT
        # ==================================

        if mode == "subscription":

            session = stripe.checkout.Session.create(

                mode="subscription",

                customer=customer_id,

                payment_method_types=["card"],

                line_items=[
                    {
                        "price": STRIPE_PRICE_ID,
                        "quantity": 1
                    }
                ],

                success_url=f"{FRONTEND_URL}/dashboard?checkout=success",

                cancel_url=f"{FRONTEND_URL}/pricing?checkout=cancelled",

                metadata={
                    "type": "subscription",
                    "plan": "pro",
                    "user_id": str(current_user.id),
                    "organization_id": str(current_user.organization_id),
                }
            )

            print("\n✅ SUBSCRIPTION SESSION CREATED")
            print("SESSION:", session.id)
            print("USER:", current_user.id)
            print("ORG:", current_user.organization_id)

            return {
                "url": session.url,
                "session_id": session.id
            }

        # ==================================
        # REPORT PAYMENT
        # ==================================

        elif mode == "report":

            if not report_id:
                raise HTTPException(
                    status_code=400,
                    detail="report_id required"
                )

            report = db.query(Report).filter(
                Report.id == report_id
            ).first()

            if not report:
                raise HTTPException(
                    status_code=404,
                    detail="Report not found"
                )

            session = stripe.checkout.Session.create(

                mode="payment",

                customer=customer_id,

                payment_method_types=["card"],

                line_items=[
                    {
                        "price": STRIPE_REPORT_PRICE,
                        "quantity": 1
                    }
                ],

                success_url=f"{FRONTEND_URL}/dashboard?report=success",

                cancel_url=f"{FRONTEND_URL}/dashboard?report=cancelled",

                metadata={
                    "type": "report",
                    "report_id": str(report.id),
                    "user_id": str(current_user.id),
                    "organization_id": str(current_user.organization_id),
                }
            )

            report.stripe_session_id = session.id

            db.commit()

            print("\n✅ REPORT SESSION CREATED")
            print("REPORT:", report.id)

            return {
                "url": session.url,
                "session_id": session.id
            }

        # ==================================
        # INVALID MODE
        # ==================================

        raise HTTPException(
            status_code=400,
            detail="Invalid mode"
        )

    except HTTPException:
        raise

    except Exception as e:

        print("\n❌ STRIPE CHECKOUT ERROR")
        print(str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )