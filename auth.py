from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models

from database import get_db

from auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

# -----------------------------------
# ROUTER
# -----------------------------------

router = APIRouter()

security = HTTPBearer()


# -----------------------------------
# REQUEST SCHEMAS
# -----------------------------------

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


# -----------------------------------
# SIGNUP
# -----------------------------------

@router.post("/auth/signup")
def signup(
    data: SignupRequest,
    db: Session = Depends(get_db)
):

    existing = db.query(models.User).filter(
        models.User.email == data.email
    ).first()

    if existing:

        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # -----------------------------------
    # CREATE ORGANIZATION
    # -----------------------------------

    org_name = data.name or data.email.split("@")[0]

    org = models.Organization(
        name=f"{org_name}_org"
    )

    db.add(org)

    db.commit()

    db.refresh(org)

    # -----------------------------------
    # CREATE USER
    # -----------------------------------

    user = models.User(
        email=data.email,
        password_hash=hash_password(data.password),
        organization_id=org.id,
        is_admin=True,
        is_active=True
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    # -----------------------------------
    # CREATE FREE SUBSCRIPTION
    # -----------------------------------

    subscription = models.Subscription(
        org_id=org.id,
        plan="free",
        status="inactive",
        is_active=False
    )

    db.add(subscription)

    db.commit()

    # -----------------------------------
    # TOKEN
    # -----------------------------------

    token = create_access_token(user)

    return {
        "message": "User created successfully",
        "access_token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "organization_id": user.organization_id,
            "is_active": user.is_active
        }
    }


# -----------------------------------
# LOGIN
# -----------------------------------

@router.post("/auth/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.email == data.email
    ).first()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "organization_id": user.organization_id,
            "is_active": user.is_active
        }
    }


# -----------------------------------
# CURRENT USER
# -----------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    payload = verify_token(token)

    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    user = db.query(models.User).filter(
        models.User.id == int(user_id)
    ).first()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# -----------------------------------
# CURRENT SESSION INFO
# -----------------------------------

@router.get("/me")
def get_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # -----------------------------------
    # ONLY ACTIVE SUBSCRIPTION
    # -----------------------------------

    subscription = db.query(models.Subscription).filter(
        models.Subscription.org_id == current_user.organization_id,
        models.Subscription.is_active == True
    ).first()

    plan = "free"

    subscription_active = False

    if subscription:

        plan = subscription.plan

        subscription_active = subscription.is_active

    return {
        "id": current_user.id,
        "email": current_user.email,
        "organization_id": current_user.organization_id,
        "plan": plan,
        "subscription_active": subscription_active,
        "is_active": current_user.is_active
    }