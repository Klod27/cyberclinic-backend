from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import hash_password, verify_password, create_access_token

router = APIRouter()

# ----------------------------------
# REGISTER
# ----------------------------------
@router.post("/auth/signup")
def signup(data: dict, db: Session = Depends(get_db)):

    email = data.get("email")
    password = data.get("password")

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(password)

    new_user = User(
        email=email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


# ----------------------------------
# LOGIN
# ----------------------------------
@router.post("/auth/login")
def login(data: dict, db: Session = Depends(get_db)):

    email = data.get("email")
    password = data.get("password")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ THIS WAS YOUR BUG
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }