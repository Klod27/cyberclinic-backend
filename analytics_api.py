from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import AssessmentResult

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/trend/{organization_id}")
def get_trend(organization_id: int, db: Session = Depends(get_db)):

    results = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.organization_id == organization_id)
        .order_by(AssessmentResult.created_at)
        .all()
    )

    return [
        {
            "date": r.created_at.strftime("%Y-%m-%d"),
            "score": r.overall_score,
            "risk": r.risk_level
        }
        for r in results
    ]