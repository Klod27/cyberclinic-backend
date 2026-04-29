from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import Subscription


def require_active_subscription(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = db.query(Subscription).filter(
        Subscription.org_id == current_user.organization_id,
        Subscription.is_active == True
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=403,
            detail="Active subscription required"
        )

    return current_user