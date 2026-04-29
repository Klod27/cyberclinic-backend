import os
import stripe
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, Subscription, Report

# ----------------------------------
# STRIPE CONFIG
# ----------------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

print("✅ Stripe Secret Loaded:", bool(stripe.api_key))
print("✅ Webhook Secret Loaded:", bool(WEBHOOK_SECRET))

# ----------------------------------
# ROUTER
# ----------------------------------
router = APIRouter()

# ----------------------------------
# 🔥 STRIPE WEBHOOK (PRODUCTION READY)
# ----------------------------------
@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    # ----------------------------------
    # VERIFY SIGNATURE
    # ----------------------------------
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        print("❌ Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        print("❌ Webhook error:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    print("\n🔥 ===== WEBHOOK RECEIVED =====")
    print("📩 Event:", event["type"])

    try:

        # ==================================
        # ✅ PAYMENT SUCCESS (CHECKOUT)
        # ==================================
        if event["type"] == "checkout.session.completed":

            session = event["data"]["object"]
            metadata = session.get("metadata", {})

            user_id = metadata.get("user_id")
            org_id = metadata.get("organization_id")
            report_id = metadata.get("report_id")
            payment_type = metadata.get("type")

            customer_id = session.get("customer")
            subscription_id = session.get("subscription")

            print("💰 PAYMENT SUCCESS")
            print("User:", user_id)
            print("Org:", org_id)
            print("Type:", payment_type)

            # ----------------------------------
            # 🔐 ACTIVATE USER
            # ----------------------------------
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    user.is_active = True
                    user.stripe_customer_id = customer_id
                    print("✅ User activated")

            # ----------------------------------
            # 💰 UNLOCK REPORT
            # ----------------------------------
            if payment_type == "report":

                if report_id:
                    report = db.query(Report).filter(
                        Report.id == int(report_id)
                    ).first()
                else:
                    # fallback → unlock latest unpaid report
                    report = db.query(Report).filter(
                        Report.organization_id == int(org_id),
                        Report.is_paid == False
                    ).order_by(Report.created_at.desc()).first()

                if report:
                    report.is_paid = True
                    print("✅ Report unlocked")
                else:
                    print("⚠️ No report found to unlock")

            # ----------------------------------
            # 🔁 SUBSCRIPTION ACTIVATION
            # ----------------------------------
            if payment_type == "subscription" and org_id:

                subscription = db.query(Subscription).filter(
                    Subscription.org_id == int(org_id)
                ).first()

                if not subscription:
                    subscription = Subscription(
                        org_id=int(org_id),
                        plan="pro",
                        status="active",
                        is_active=True,
                        stripe_customer_id=customer_id,
                        stripe_subscription_id=subscription_id
                    )
                    db.add(subscription)
                else:
                    subscription.plan = "pro"
                    subscription.status = "active"
                    subscription.is_active = True
                    subscription.stripe_customer_id = customer_id
                    subscription.stripe_subscription_id = subscription_id

                print("✅ Subscription activated")

            db.commit()

        # ==================================
        # 🔁 SUBSCRIPTION RENEWAL
        # ==================================
        elif event["type"] == "invoice.payment_succeeded":

            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")

            print("💰 SUBSCRIPTION RENEWED")

            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription:
                subscription.status = "active"
                subscription.is_active = True

                # Extend access
                period_end = invoice.get("current_period_end")
                if period_end:
                    subscription.current_period_end = datetime.fromtimestamp(period_end)

                # Reactivate all org users
                users = db.query(User).filter(
                    User.organization_id == subscription.org_id
                ).all()

                for u in users:
                    u.is_active = True

                db.commit()
                print("✅ Subscription renewed")

        # ==================================
        # ❌ PAYMENT FAILED
        # ==================================
        elif event["type"] == "invoice.payment_failed":

            invoice = event["data"]["object"]
            subscription_id = invoice.get("subscription")

            print("❌ PAYMENT FAILED")

            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription:
                subscription.status = "past_due"
                subscription.is_active = False

                users = db.query(User).filter(
                    User.organization_id == subscription.org_id
                ).all()

                for u in users:
                    u.is_active = False

                db.commit()
                print("⚠️ Subscription marked past_due")

        # ==================================
        # 🚫 SUBSCRIPTION CANCELED
        # ==================================
        elif event["type"] == "customer.subscription.deleted":

            sub_data = event["data"]["object"]
            subscription_id = sub_data.get("id")

            print("🚫 SUBSCRIPTION CANCELED")

            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription:
                subscription.status = "canceled"
                subscription.is_active = False

                users = db.query(User).filter(
                    User.organization_id == subscription.org_id
                ).all()

                for u in users:
                    u.is_active = False

                db.commit()
                print("❌ Subscription canceled")

        else:
            print(f"⚠️ Unhandled event: {event['type']}")

    except Exception as e:
        db.rollback()
        print("❌ ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    print("🔥 ===== END WEBHOOK =====\n")

    return {"status": "success"}