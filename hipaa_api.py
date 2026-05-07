from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

import models

from ai_recommendations import generate_recommendations
from database import get_db
from models import HIPAAAssessment, HIPAAAnswer
from hipaa_questions import hipaa_questions
from hipaa_scoring import (
    calculate_score,
    determine_risk,
    calculate_category_scores
)

from auth import get_current_user

router = APIRouter()


# ----------------------------------
# HELPERS
# ----------------------------------

def normalize_answer(value):
    """
    Frontend may send:
      "Yes"

    or:
      {"answer": "Yes", "weight": 5, "category": "Administrative"}

    This helper safely extracts the real answer string.
    """

    if isinstance(value, dict):
        return str(value.get("answer", "")).strip()

    return str(value or "").strip()


def normalize_answers_for_storage(answers):
    """
    Converts frontend answer objects
    into simple strings for database storage.
    """

    return {
        qid: normalize_answer(value)
        for qid, value in answers.items()
    }


def safe_org_id(raw_org_id):
    """
    Prevents database crashes
    when frontend sends 'default'.
    """

    if raw_org_id in (None, "", "default"):
        return None

    try:
        return int(raw_org_id)

    except Exception:
        return None


def build_findings(answers):

    findings = []
    remediation = []

    for q in hipaa_questions:

        qid = q.get("id")

        answer = normalize_answer(
            answers.get(qid, "")
        ).lower()

        if answer in ("no", "partial"):

            severity = (
                q.get("severity") or "Medium"
            ).upper()

            finding = {
                "issue": q.get("question"),
                "title": q.get("question"),
                "severity": severity,
                "risk_level": severity,
                "category": q.get(
                    "category",
                    "General"
                ),
                "hipaa_reference": q.get(
                    "hipaa_reference"
                ),
                "description":
                    f"{q.get('question')} "
                    f"was answered as "
                    f"{answer.title()}.",
                "impact":
                    "Potential HIPAA compliance "
                    "gap requiring review.",
                "business_impact":
                    "May increase regulatory, "
                    "operational, or patient "
                    "trust risk.",
                "recommendation":
                    f"Review and implement "
                    f"control: {q.get('question')}"
            }

            findings.append(finding)

            remediation.append({
                "issue": q.get("question"),
                "recommendation":
                    finding["recommendation"],
                "priority": severity
            })

    return findings, remediation


# ----------------------------------
# GET HIPAA QUESTIONS
# BACKEND-CONTROLLED SAAS GATING
# ----------------------------------

@router.get("/hipaa/questions")
def get_questions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    subscription = db.query(
        models.Subscription
    ).filter(
        models.Subscription.org_id
        == current_user.organization_id,

        models.Subscription.is_active == True
    ).order_by(
        models.Subscription.created_at.desc()
    ).first()

    is_pro = bool(
        subscription and
        subscription.plan in [
            "pro",
            "enterprise"
        ]
    )

    # ----------------------------------
    # PRO USERS
    # ----------------------------------

    if is_pro:

        return {
            "plan": subscription.plan,
            "is_pro": True,
            "questions": hipaa_questions
        }

    # ----------------------------------
    # FREE USERS
    # ----------------------------------

    FREE_LIMIT = 10

    return {
        "plan": "free",
        "is_pro": False,
        "questions": hipaa_questions[:FREE_LIMIT]
    }


# ----------------------------------
# SUBMIT ASSESSMENT
# ----------------------------------

@router.post("/hipaa/submit")
def submit_assessment(
    data: dict,
    db: Session = Depends(get_db)
):

    try:

        print("Incoming data:", data)

        answers = data.get("answers", {})

        org_id = safe_org_id(
            data.get("org_id")
        )

        if not answers:

            raise HTTPException(
                status_code=400,
                detail="Missing answers"
            )

        # ----------------------------------
        # SCORING
        # ----------------------------------

        score = calculate_score(answers)

        category_scores = (
            calculate_category_scores(
                answers
            )
        )

        risk_level = determine_risk(score)

        # ----------------------------------
        # FINDINGS + REMEDIATION
        # ----------------------------------

        findings, remediation = (
            build_findings(answers)
        )

        # ----------------------------------
        # AI RECOMMENDATIONS
        # ----------------------------------

        try:

            ai_recommendations = (
                generate_recommendations({
                    "score": score,
                    "risk_level": risk_level,
                    "issues": findings
                })
            )

        except Exception as ai_error:

            print(
                "AI recommendation error:",
                str(ai_error)
            )

            ai_recommendations = [
                "Review all failed or partial HIPAA controls.",
                "Prioritize critical and high-severity findings.",
                "Document remediation actions and reassess regularly."
            ]

        # ----------------------------------
        # SAVE ASSESSMENT
        # ----------------------------------

        assessment_id = str(uuid.uuid4())

        try:

            assessment = HIPAAAssessment(
                organization_id=org_id,
                score=score,
                risk_level=risk_level
            )

            db.add(assessment)

            db.commit()

            db.refresh(assessment)

            assessment_id = assessment.id

            simple_answers = (
                normalize_answers_for_storage(
                    answers
                )
            )

            for q_id, answer_value in (
                simple_answers.items()
            ):

                db.add(
                    HIPAAAnswer(
                        assessment_id=assessment.id,
                        question_id=q_id,
                        answer=answer_value
                    )
                )

            db.commit()

        except Exception as db_error:

            db.rollback()

            print(
                "Database save skipped:",
                str(db_error)
            )

        # ----------------------------------
        # RESPONSE
        # ----------------------------------

        report_data = {

            "assessment_id": assessment_id,

            "scan_id": str(assessment_id),

            "score": score,

            "risk": risk_level,

            "risk_level": risk_level,

            "category_scores":
                category_scores,

            "findings": findings,

            "remediation": remediation,

            "ai_recommendations":
                ai_recommendations
        }

        return {

            "status": "success",

            "scan_id": str(assessment_id),

            "assessment_id":
                assessment_id,

            "data": report_data,

            **report_data
        }

    except HTTPException:
        raise

    except Exception as e:

        print("🔥 ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ----------------------------------
# GET RESULTS
# ----------------------------------

@router.get("/hipaa/results/{assessment_id}")
def get_results(
    assessment_id: int,
    db: Session = Depends(get_db)
):

    assessment = db.query(
        HIPAAAssessment
    ).filter(
        HIPAAAssessment.id == assessment_id
    ).first()

    if not assessment:

        raise HTTPException(
            status_code=404,
            detail="Assessment not found"
        )

    answers = db.query(
        HIPAAAnswer
    ).filter(
        HIPAAAnswer.assessment_id
        == assessment_id
    ).all()

    answers_dict = {

        a.question_id: a.answer
        for a in answers
    }

    category_scores = (
        calculate_category_scores(
            answers_dict
        )
    )

    findings, remediation = (
        build_findings(answers_dict)
    )

    try:

        ai_recommendations = (
            generate_recommendations({
                "score": assessment.score,
                "risk_level":
                    assessment.risk_level,
                "issues": findings
            })
        )

    except Exception:

        ai_recommendations = [
            "Review failed controls.",
            "Prioritize high-risk remediation.",
            "Repeat assessment after mitigation."
        ]

    return {

        "assessment": {

            "id": assessment.id,

            "score": assessment.score,

            "risk": assessment.risk_level,

            "risk_level":
                assessment.risk_level,

            "category_scores":
                category_scores
        },

        "answers": answers_dict,

        "findings": findings,

        "remediation": remediation,

        "ai_recommendations":
            ai_recommendations
    }