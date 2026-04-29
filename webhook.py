import os
import stripe
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# ✅ Stripe config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


@router.post("/webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )

    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ----------------------------------
    # HANDLE EVENTS
    # ----------------------------------

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        print("✅ PAYMENT SUCCESS")
        print("User ID:", session.get("metadata", {}).get("user_id"))

    elif event["type"] == "invoice.payment_succeeded":
        print("💰 Subscription payment succeeded")

    # ----------------------------------
    # REQUIRED RESPONSE
    # ----------------------------------
    return {"status": "success"}