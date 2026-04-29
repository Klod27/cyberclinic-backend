from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Subscription
from auth import get_current_user

router = APIRouter()

@router.get("/subscription/status")
def get_subscription_status(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    sub = db.query(Subscription).filter(
        Subscription.org_id == user.organization_id
    ).order_by(Subscription.created_at.desc()).first()

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