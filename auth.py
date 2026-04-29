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

router = APIRouter()

# ----------------------------------
# 🔐 SECURITY (FIXED)
# ----------------------------------
security = HTTPBearer()


# ----------------------------------
# REQUEST MODELS
# ----------------------------------
class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ----------------------------------
# SIGNUP
# ----------------------------------
@router.post("/auth/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):

    existing = db.query(models.User).filter(models.User.email == data.email).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # CREATE ORGANIZATION
    org = models.Organization(
        name=f"{data.email.split('@')[0]}_org"
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # HASH PASSWORD
    hashed = hash_password(data.password)

    # CREATE USER
    user = models.User(
        email=data.email,
        password_hash=hashed,
        organization_id=org.id,
        is_admin=True,

        # TEMP ACCESS ENABLED
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully"}


# ----------------------------------
# LOGIN
# ----------------------------------
@router.post("/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)

    return {"access_token": token}


# ----------------------------------
# 🔐 GET CURRENT USER (FIXED)
# ----------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ----------------------------------
# /me ENDPOINT
# ----------------------------------
@router.get("/me")
def get_me(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    subscription = db.query(models.Subscription).filter(
        models.Subscription.org_id == current_user.organization_id
    ).first()

    is_active = False

    if subscription and subscription.is_active:
        is_active = True

    # TEMP fallback (until Stripe active)
    if current_user.is_active:
        is_active = True

    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": is_active
    }