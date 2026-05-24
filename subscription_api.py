from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Subscription
from auth import get_current_user

router = APIRouter()


# =========================================
# GET SUBSCRIPTION STATUS
# =========================================

@router.get("/subscription/status")
def get_subscription_status(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    # -----------------------------------------
    # GET MOST RECENT SUBSCRIPTION
    # -----------------------------------------

    sub = db.query(Subscription).filter(
        Subscription.org_id == user.organization_id
    ).order_by(
        Subscription.created_at.desc()
    ).first()

    # -----------------------------------------
    # DEFAULT FREE PLAN
    # -----------------------------------------

    if not sub:

        return {
            "plan": "free",
            "status": "inactive",
            "is_active": False
        }

    # -----------------------------------------
    # RETURN SUBSCRIPTION
    # -----------------------------------------

    return {
        "plan": sub.plan,
        "status": sub.status,
        "is_active": sub.is_active
    }


# =========================================
# TEST PRO ACTIVATION
# =========================================

@router.post("/subscription/activate-test")
def activate_test_subscription(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    # -----------------------------------------
    # REMOVE OLD SUBSCRIPTIONS
    # -----------------------------------------

    db.query(Subscription).filter(
        Subscription.org_id == user.organization_id
    ).delete()

    db.commit()

    # -----------------------------------------
    # CREATE NEW ACTIVE PRO SUBSCRIPTION
    # -----------------------------------------

    sub = Subscription(
        org_id=user.organization_id,
        plan="pro",
        status="active",
        is_active=True
    )

    db.add(sub)

    db.commit()

    db.refresh(sub)

    # -----------------------------------------
    # VERIFY DATABASE SAVE
    # -----------------------------------------

    saved = db.query(Subscription).filter(
        Subscription.org_id == user.organization_id
    ).order_by(
        Subscription.created_at.desc()
    ).first()

    return {
        "message": "Pro subscription activated successfully",
        "subscription": {
            "org_id": saved.org_id,
            "plan": saved.plan,
            "status": saved.status,
            "is_active": saved.is_active
        }
    }