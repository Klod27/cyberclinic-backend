from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_recommendations import generate_recommendations
from database import get_db
from models import HIPAAAssessment, HIPAAAnswer
from hipaa_questions import hipaa_questions
from hipaa_scoring import calculate_score, determine_risk, calculate_category_scores

from auth import get_current_user

router = APIRouter()


# ----------------------------------
# GET HIPAA QUESTIONS (AUTH ONLY)
# ----------------------------------
@router.get("/hipaa/questions")
def get_questions():
    return hipaa_questions


# ----------------------------------
# SUBMIT ASSESSMENT (AUTH ONLY)
# ----------------------------------
@router.post("/hipaa/submit")
def submit_assessment(
    data: dict,
    db: Session = Depends(get_db)
):

    try:
        print("Incoming data:", data)

        answers = data.get("answers")

        if not answers:
            raise HTTPException(status_code=400, detail="Missing answers")

        # ----------------------------------
        # SCORING
        # ----------------------------------
        score = calculate_score(answers)
        category_scores = calculate_category_scores(answers)
        risk_level = determine_risk(score)

        # ----------------------------------
        # BUILD FINDINGS (FIXED)
        # ----------------------------------
        findings = []

        for q in hipaa_questions:
            answer = answers.get(q["id"], "").lower()

            if answer == "no":
                findings.append({
                    "issue": q["question"],
                    "severity": (q.get("severity") or "MEDIUM").upper(),
                    "recommendation": f"Implement control: {q['question']}",
                    "hipaa_reference": q.get("hipaa_reference")
                })

        # ----------------------------------
        # AI RECOMMENDATIONS
        # ----------------------------------
        ai_recommendations = generate_recommendations({
            "issues": findings
        })

        # ----------------------------------
        # SAVE ASSESSMENT
        # ----------------------------------
        assessment = HIPAAAssessment(
            organization_id=user.organization_id,
            score=score,
            risk_level=risk_level
        )

        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        # ----------------------------------
        # SAVE ANSWERS
        # ----------------------------------
        for q_id, answer in answers.items():
            db.add(HIPAAAnswer(
                assessment_id=assessment.id,
                question_id=q_id,
                answer=answer
            ))

        db.commit()

        # ----------------------------------
        # RETURN RESPONSE (FIXED)
        # ----------------------------------
        return {
            "assessment_id": assessment.id,
            "score": score,
            "risk_level": risk_level,
            "category_scores": category_scores,

            # ✅ THIS IS WHAT YOUR FRONTEND NEEDS
            "findings": findings,

            # ✅ CLEAN AI OUTPUT
            "ai_recommendations": ai_recommendations
        }

    except Exception as e:
        print("🔥 ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------
# GET RESULTS (AUTH ONLY)
# ----------------------------------
@router.get("/hipaa/results/{assessment_id}")
def get_results(
    assessment_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    assessment = db.query(HIPAAAssessment).filter(
        HIPAAAssessment.id == assessment_id,
        HIPAAAssessment.organization_id == user.organization_id
    ).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    answers = db.query(HIPAAAnswer).filter(
        HIPAAAnswer.assessment_id == assessment_id
    ).all()

    answers_dict = {a.question_id: a.answer for a in answers}

    category_scores = calculate_category_scores(answers_dict)

    findings = []

    for q in hipaa_questions:
        if answers_dict.get(q["id"], "").lower() == "no":
            findings.append({
                "issue": q["question"],
                "severity": (q.get("severity") or "MEDIUM").upper(),
                "recommendation": f"Implement control: {q['question']}",
                "hipaa_reference": q.get("hipaa_reference")
            })

    ai_recommendations = generate_recommendations({
        "issues": findings
    })

    return {
        "assessment": {
            "id": assessment.id,
            "score": assessment.score,
            "risk_level": assessment.risk_level,
            "category_scores": category_scores
        },
        "answers": answers_dict,

        # ✅ FIXED STRUCTURE
        "findings": findings,
        "ai_recommendations": ai_recommendations
    }