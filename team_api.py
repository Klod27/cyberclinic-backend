from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_current_user

router = APIRouter()

# ----------------------------------
# GET TEAM MEMBERS
# ----------------------------------
@router.get("/team")
def get_team(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    members = db.query(User).filter(
        User.organization_id == user.organization_id
    ).all()

    return [
        {
            "id": m.id,
            "email": m.email,
            "role": m.role
        }
        for m in members
    ]


# ----------------------------------
# INVITE USER (ADMIN ONLY)
# ----------------------------------
@router.post("/team/invite")
def invite_user(
    email: str,
    role: str = "staff",
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    if user.role != "admin":
        raise HTTPException(403, "Admins only")

    new_user = User(
        email=email,
        password="temp123",  # simple for now
        organization_id=user.organization_id,
        role=role
    )

    db.add(new_user)
    db.commit()

    return {"message": "User invited"}


# ----------------------------------
# CHANGE ROLE (ADMIN ONLY)
# ----------------------------------
@router.post("/team/role")
def change_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    if user.role != "admin":
        raise HTTPException(403, "Admins only")

    target = db.query(User).filter(User.id == user_id).first()

    if not target:
        raise HTTPException(404, "User not found")

    target.role = role
    db.commit()

    return {"message": "Role updated"}