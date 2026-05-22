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

    sub = db.query(Subscription).filter(
        Subscription.org_id == user.organization_id
    ).order_by(
        Subscription.created_at.desc()
    ).first()

    if not sub:
        return {
            "plan": "free",
            "status": "inactive",
            "is_active": False
        }

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

    # Remove old subscriptions
    db.query(Subscription).filter(
        Subscription.org_id == user.organization_id
    ).delete()

    # Create new PRO subscription
    sub = Subscription(
        org_id=user.organization_id,
        plan="pro",
        status="active",
        is_active=True
    )

    db.add(sub)
    db.commit()

    return {
        "message": "Pro subscription activated successfully"
    }