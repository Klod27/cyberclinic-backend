from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Organization, User
from auth import get_current_user

router = APIRouter()


# ----------------------------------
# CREATE ORGANIZATION / CLINIC
# ----------------------------------
@router.post("/org/create")
def create_org(
    name: str,
    parent_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if not name or name.strip() == "":
        raise HTTPException(status_code=400, detail="Organization name required")

    # 🔒 Only admins can create child clinics
    if parent_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    org = Organization(
        name=name.strip(),
        parent_id=parent_id
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    # If creating root org, assign user
    if parent_id is None:
        current_user.organization_id = org.id
        db.commit()

    return {
        "message": "Organization created",
        "org_id": org.id
    }


# ----------------------------------
# GET ORGANIZATIONS (PARENT + CHILDREN)
# ----------------------------------
@router.get("/org/list")
def list_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    base_org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()

    if not base_org:
        return []

    # 🔥 If parent org → return all children
    if base_org.parent_id is None:

        children = db.query(Organization).filter(
            Organization.parent_id == base_org.id
        ).all()

        return [
            {
                "id": base_org.id,
                "name": base_org.name,
                "parent_id": None
            }
        ] + [
            {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id
            }
            for c in children
        ]

    # 🔥 If child org → return itself only
    return [
        {
            "id": base_org.id,
            "name": base_org.name,
            "parent_id": base_org.parent_id
        }
    ]


# ----------------------------------
# SWITCH ORGANIZATION
# ----------------------------------
@router.post("/org/switch")
def switch_org(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    target = db.query(Organization).filter(
        Organization.id == org_id
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="Organization not found")

    current_org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()

    # 🔒 SECURITY: allow switching only within hierarchy
    allowed = (
        target.id == current_org.id or
        target.parent_id == current_org.id or
        current_org.parent_id == target.id
    )

    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")

    current_user.organization_id = target.id
    db.commit()

    return {"message": "Switched organization"}