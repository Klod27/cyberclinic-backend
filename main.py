from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from datetime import datetime
import logging
import os
import uuid

import models

# DATABASE
from database import engine, get_db, Base

# AUTH
from auth import router as auth_router, get_current_user

# ROUTERS
from billing import router as billing_router
from stripe_webhook import router as stripe_webhook_router
from team_api import router as team_router
from subscription_api import router as subscription_router
from analytics_api import router as analytics_router
from organization_api import router as org_router
from automation_api import router as automation_router
from report_api import router as report_router
from hipaa_api import router as hipaa_router

# MODELS
from models import AssessmentResult

# QUESTIONS
from hipaa_questions import hipaa_questions

# REPORTLAB
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# =====================================================
# DATABASE INIT
# =====================================================

Base.metadata.create_all(bind=engine)

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="CyberClinic API",
    version="4.0.0"
)

# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ROUTERS
# =====================================================

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(report_router)
app.include_router(hipaa_router)
app.include_router(stripe_webhook_router)
app.include_router(automation_router)
app.include_router(org_router)
app.include_router(team_router)
app.include_router(subscription_router)
app.include_router(analytics_router)

# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {"message": "CyberClinic API running"}

# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():
    return {"status": "healthy"}

# =====================================================
# HIPAA QUESTIONS
# =====================================================

@app.get("/hipaa/questions")
def get_questions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    subscription = db.query(models.Subscription).filter(
        models.Subscription.org_id == current_user.organization_id,
        models.Subscription.is_active == True,
        models.Subscription.status == "active"
    ).first()

    logger.info(f"USER ORG: {current_user.organization_id}")
    logger.info(f"SUBSCRIPTION FOUND: {subscription}")

    is_pro = (
        subscription is not None and
        subscription.plan in ["pro", "enterprise"]
    )

    iif subscription:
    return {
        "plan": subscription.plan or "pro",
        "questions": hipaa_questions
    }

    return {
        "plan": "pro",
        "questions": hipaa_questions
}

# =====================================================
# CONTROL MAP
# =====================================================

CONTROL_MAP = {
    1: {
        "control_id": "IA-2",
        "title": "Multi-Factor Authentication",
        "hipaa": "45 CFR §164.312(d)",
        "severity": "CRITICAL",
        "recommendation": "Enable MFA for all privileged users"
    },
    2: {
        "control_id": "SC-13",
        "title": "Encryption at Rest",
        "hipaa": "45 CFR §164.312(a)(2)(iv)",
        "severity": "CRITICAL",
        "recommendation": "Encrypt all PHI at rest"
    },
    3: {
        "control_id": "AU-2",
        "title": "Audit Logging",
        "hipaa": "45 CFR §164.312(b)",
        "severity": "HIGH",
        "recommendation": "Enable system audit logging"
    },
    4: {
        "control_id": "AC-2",
        "title": "Access Control",
        "hipaa": "45 CFR §164.308(a)(4)",
        "severity": "HIGH",
        "recommendation": "Enforce least privilege access"
    }
}

# =====================================================
# SCORING ENGINE
# =====================================================

def calculate_score(answers):

    total_weight = 0
    earned_weight = 0

    category_totals = {}
    category_earned = {}

    findings = []
    remediation = []

    for qid, obj in answers.items():

        weight = obj.get("weight", 5)
        category = obj.get("category", "General")
        answer = obj.get("answer")

        total_weight += weight

        category_totals.setdefault(category, 0)
        category_earned.setdefault(category, 0)

        category_totals[category] += weight

        if answer == "Yes":
            earned = weight
        elif answer == "Partial":
            earned = weight * 0.5
        else:
            earned = 0

        earned_weight += earned
        category_earned[category] += earned

        if answer != "Yes":

            control = CONTROL_MAP.get(int(qid), {})

            severity = control.get("severity", "MEDIUM")

            findings.append({
                "issue": control.get("title", f"Control {qid}"),
                "control_id": control.get("control_id", f"CTRL-{qid}"),
                "hipaa_reference": control.get("hipaa", "HIPAA"),
                "severity": severity,
                "category": category,
                "status": "FAIL" if answer == "No" else "PARTIAL",
                "description": f"{control.get('title', 'Control')} not fully implemented"
            })

            remediation.append({
                "issue": control.get("title"),
                "recommendation": control.get("recommendation"),
                "priority": severity
            })

    score = round(
        (earned_weight / total_weight) * 100,
        2
    ) if total_weight else 0

    category_scores = {
        cat: round(
            (category_earned[cat] / category_totals[cat]) * 100,
            2
        )
        for cat in category_totals
    }

    if score >= 85:
        risk = "LOW"
    elif score >= 60:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    return (
        score,
        risk,
        category_scores,
        findings,
        remediation
    )

# =====================================================
# HIPAA SUBMIT
# =====================================================

@app.post("/hipaa/submit")
def submit_hipaa_assessment(
    payload: dict,
    db: Session = Depends(get_db)
):

    try:

        answers = payload.get("answers", {})
        org_id = payload.get("org_id")

        if not answers:
            raise HTTPException(
                status_code=400,
                detail="No answers provided"
            )

        (
            score,
            risk,
            category_scores,
            findings,
            remediation
        ) = calculate_score(answers)

        result = AssessmentResult(
            organization_id=org_id,
            overall_score=score,
            risk_level=risk,
            created_at=datetime.utcnow()
        )

        db.add(result)
        db.commit()
        db.refresh(result)

        return {
            "status": "success",
            "data": {
                "score": score,
                "risk": risk,
                "category_scores": category_scores,
                "findings": findings,
                "remediation": remediation,
                "assessment_id": result.id
            }
        }

    except Exception as e:

        logger.error(str(e))

        raise HTTPException(
            status_code=500,
            detail="Assessment failed"
        )

# =====================================================
# PDF REPORT GENERATION
# =====================================================

@app.post("/reports/generate")
def generate_pdf_report(
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    subscription = db.query(models.Subscription).filter(
        models.Subscription.org_id == current_user.organization_id,
        models.Subscription.is_active == True,
        models.Subscription.status == "active"
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=403,
            detail="Upgrade required"
        )

    data = payload.get("data", {})

    score = data.get("score", 0)
    risk = data.get("risk", "UNKNOWN")

    report_id = str(uuid.uuid4())

    os.makedirs("reports", exist_ok=True)

    file_path = f"reports/{report_id}.pdf"

    doc = SimpleDocTemplate(file_path)

    styles = getSampleStyleSheet()

    elements = []

    # TITLE

    elements.append(
        Paragraph(
            "CyberClinic HIPAA Compliance Report",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 20))

    # SUMMARY TABLE

    summary = [
        ["Metric", "Value"],
        ["Score", f"{score}%"],
        ["Risk Level", risk],
        ["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")]
    ]

    table = Table(summary)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 20))

    # CATEGORY SCORES

    elements.append(
        Paragraph(
            "Category Breakdown",
            styles["Heading2"]
        )
    )

    for cat, val in data.get("category_scores", {}).items():

        elements.append(
            Paragraph(
                f"{cat}: {val}%",
                styles["Normal"]
            )
        )

    elements.append(Spacer(1, 20))

    # FINDINGS

    elements.append(
        Paragraph(
            "Key Findings",
            styles["Heading2"]
        )
    )

    findings = data.get("findings", [])

    if not findings:

        elements.append(
            Paragraph(
                "No major findings identified.",
                styles["Normal"]
            )
        )

    for f in findings:

        elements.append(
            Paragraph(
                f"{f.get('issue')} ({f.get('severity')})",
                styles["Normal"]
            )
        )

    elements.append(Spacer(1, 20))

    # REMEDIATION

    elements.append(
        Paragraph(
            "Recommended Remediation",
            styles["Heading2"]
        )
    )

    remediation = data.get("remediation", [])

    if not remediation:

        elements.append(
            Paragraph(
                "No remediation required.",
                styles["Normal"]
            )
        )

    for r in remediation:

        elements.append(
            Paragraph(
                f"{r.get('issue')} — {r.get('recommendation')}",
                styles["Normal"]
            )
        )

    elements.append(Spacer(1, 30))

    elements.append(
        Paragraph(
            "Generated by CyberClinic AI Compliance Engine",
            styles["Italic"]
        )
    )

    doc.build(elements)

    return {
        "status": "success",
        "report_id": report_id,
        "download_url": f"/reports/download/{report_id}"
    }

# =====================================================
# DOWNLOAD REPORT
# =====================================================

@app.get("/reports/download/{report_id}")
def download_report(report_id: str):

    file_path = f"reports/{report_id}.pdf"

    if not os.path.exists(file_path):

        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return FileResponse(
        file_path,
        media_type="application/pdf"
    )

# =====================================================
# REPORT HISTORY
# =====================================================

@app.get("/reports/history")
def get_report_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    results = db.query(AssessmentResult)\
        .filter(
            AssessmentResult.organization_id ==
            current_user.organization_id
        )\
        .order_by(
            AssessmentResult.created_at.desc()
        )\
        .all()

    return {
        "history": [
            {
                "id": r.id,
                "score": r.overall_score,
                "risk": r.risk_level,
                "date": r.created_at.isoformat()
            }
            for r in results
        ]
    }