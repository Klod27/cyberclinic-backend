from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
import uuid
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Routers
from team_api import router as team_router
from subscription_api import router as subscription_router
from analytics_api import router as analytics_router
from organization_api import router as org_router
from automation_api import router as automation_router
from billing import router as billing_router
from stripe_webhook import router as stripe_webhook_router
from report_api import router as report_router
from auth import router as auth_router, get_current_user
from hipaa_api import router as hipaa_router

# DB
from database import engine, get_db, Base
from models import AssessmentResult
from hipaa_questions import hipaa_questions
# ----------------------------------
# LOGGING
# ----------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------
# DATABASE
# ----------------------------------
Base.metadata.create_all(bind=engine)

# ----------------------------------
# APP
# ----------------------------------
app = FastAPI(title="CyberClinic API", version="4.0.0")
@app.get("/hipaa/questions")
def get_questions():
    return {"questions": hipaa_questions}
# ----------------------------------
# CORS
# ----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------
# ROUTERS
# ----------------------------------
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

# ----------------------------------
# ROOT
# ----------------------------------
@app.get("/")
def root():
    return {"message": "CyberClinic API running"}

# ----------------------------------
# HEALTH
# ----------------------------------
@app.get("/health")
def health():
    return {"status": "healthy"}

# ----------------------------------
# 🔥 CONTROL MAP (REAL HIPAA LOGIC)
# ----------------------------------

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

# ----------------------------------
# 🔥 SCORING ENGINE
# ----------------------------------

def calculate_score(answers):

    total_weight = 0
    earned_weight = 0

    category_totals = {}
    category_earned = {}

    findings = []
    remediation = []

    for qid, obj in answers.items():

        qid_str = str(qid)

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

            control = {}

            severity = control.get("severity", "MEDIUM")

            if answer == "No" and severity != "CRITICAL":
                severity = "HIGH"

            findings.append({
                "issue": control.get("title", f"Control {qid}"),
                "control_id": control.get("control_id", f"CTRL-{qid}"),
                "hipaa_reference": control.get("hipaa", "HIPAA Standard"),
                "severity": severity,
                "category": category,
                "status": "FAIL" if answer == "No" else "PARTIAL",
                "description": f"{control.get('title')} not fully implemented"
            })

            remediation.append({
                "issue": control.get("title"),
                "recommendation": control.get("recommendation"),
                "priority": severity
            })

    score = round((earned_weight / total_weight) * 100, 2) if total_weight else 0

    category_scores = {
        cat: round((category_earned[cat] / category_totals[cat]) * 100, 2)
        for cat in category_totals
    }

    if score >= 85:
        risk = "LOW"
    elif score >= 60:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    return score, risk, category_scores, findings, remediation

# ----------------------------------
# 🔥 HIPAA SUBMIT (FINAL)
# ----------------------------------

@app.post("/hipaa/submit")
def submit_hipaa_assessment(
    payload: dict,
    db: Session = Depends(get_db)
):

    try:
        answers = payload.get("answers", {})
        org_id = payload.get("org_id", None)

        if not answers:
            raise HTTPException(status_code=400, detail="No answers provided")

        score, risk, category_scores, findings, remediation = calculate_score(answers)

        result = AssessmentResult(
            user_id=1,
            organization_id=org_id,
            overall_score=score,
            risk_level=risk,
            created_at=datetime.utcnow()
        )

        db.add(result)
        db.commit()

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
        raise HTTPException(status_code=500, detail="Assessment failed")
    
def build_category_chart(category_scores):
    drawing = Drawing(400, 200)

    data = [list(category_scores.values())]
    categories = list(category_scores.keys())

    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 50
    chart.height = 125
    chart.width = 300

    chart.data = data
    chart.categoryAxis.categoryNames = categories

    chart.bars[0].fillColor = colors.HexColor("#3b82f6")

    drawing.add(chart)

    return drawing

def get_risk_color(score):
    if score >= 85:
        return colors.green
    elif score >= 60:
        return colors.orange
    return colors.red
# ----------------------------------
# 🔥 PDF REPORT
# ----------------------------------
from reportlab.platypus import (
     SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

@app.post("/reports/generate")
def generate_pdf_report(
    payload: dict,
    current_user=Depends(get_current_user)
):

    # ✅ SAFE PAYWALL
    if getattr(current_user, "plan", "free") != "pro":
        raise HTTPException(status_code=403, detail="Upgrade required")

    data = payload.get("data", {})

    score = data.get("score", 0)
    risk = data.get("risk", "UNKNOWN")

    report_id = str(uuid.uuid4())
    file_path = f"reports/{report_id}.pdf"

    os.makedirs("reports", exist_ok=True)

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    # HEADER
    elements.append(Paragraph(
        "<b>CyberClinic HIPAA Compliance Report</b>",
        styles["Title"]
    ))

    elements.append(Spacer(1, 15))

    # SUMMARY
    summary = [
        ["Metric", "Value"],
        ["Score", f"{score}%"],
        ["Risk", risk],
        ["Date", data.get("timestamp", "N/A")]
    ]

    table = Table(summary)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(table)

    elements.append(Spacer(1, 20))

    # CATEGORY
    elements.append(Paragraph("<b>Category Breakdown</b>", styles["Heading2"]))

    for cat, val in data.get("category_scores", {}).items():
        elements.append(Paragraph(f"{cat}: {val}%", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # FINDINGS
    elements.append(Paragraph("<b>Findings</b>", styles["Heading2"]))

    for f in data.get("findings", []):
        elements.append(Paragraph(
            f"{f.get('issue')} ({f.get('severity')})",
            styles["Normal"]
        ))

    elements.append(Spacer(1, 20))

    # REMEDIATION
    elements.append(Paragraph("<b>Remediation</b>", styles["Heading2"]))

    for r in data.get("remediation", []):
        elements.append(Paragraph(
            f"{r.get('issue')} — {r.get('recommendation')}",
            styles["Normal"]
        ))

    doc.build(elements)

    return {
        "status": "success",
        "report_id": report_id,
        "download_url": f"/reports/download/{report_id}"
    }
    # ---------------------------
    # FOOTER
    # ---------------------------
    elements.append(Paragraph(
        "<i>Generated by CyberClinic AI Compliance Platform</i>",
        styles["Normal"]
    ))

    doc.build(elements)

    return {
        "status": "success",
        "report_id": report_id,
        "download_url": f"/reports/download/{report_id}"
    }
    # ---------------------------
    # TITLE
    # ---------------------------
    elements.append(Paragraph(
        "<b>CyberClinic HIPAA Compliance Assessment Report</b>",
        styles["Title"]
    ))

    elements.append(Spacer(1, 12))

    # ---------------------------
    # EXECUTIVE SUMMARY
    # ---------------------------
    
    score = data.get("score", 0)
    risk = data.get("risk", "UNKNOWN")

    elements.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))

    elements.append(Paragraph(
        f"This report evaluates your organization's compliance posture "
        f"against HIPAA Security Rule safeguards.",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Overall Score:</b> {score}%", styles["Normal"]))
    elements.append(Paragraph(f"<b>Risk Level:</b> {risk}", styles["Normal"]))

    elements.append(Spacer(1, 15))

    # ---------------------------
    # CATEGORY SCORES
    # ---------------------------
    elements.append(Paragraph("<b>Category Breakdown</b>", styles["Heading2"]))

    for cat, val in data.get("category_scores", {}).items():
        elements.append(Paragraph(f"{cat}: {val}%", styles["Normal"]))

    elements.append(Spacer(1, 15))

    # ---------------------------
    # FINDINGS
    # ---------------------------
    elements.append(Paragraph("<b>Key Findings</b>", styles["Heading2"]))

    findings = data.get("findings", [])

    if not findings:
        elements.append(Paragraph("No major findings identified.", styles["Normal"]))

    for f in findings:

        severity = f.get("severity", "MEDIUM")

        elements.append(Paragraph(
            f"<b>{f.get('issue')}</b> ({severity})",
            styles["Normal"]
        ))

        elements.append(Paragraph(
            f"Control: {f.get('control_id')} | HIPAA: {f.get('hipaa_reference')}",
            styles["Normal"]
        ))

        elements.append(Paragraph(
            f"Description: {f.get('description')}",
            styles["Normal"]
        ))

        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 15))

    # ---------------------------
    # REMEDIATION PLAN
    # ---------------------------
    elements.append(Paragraph("<b>Recommended Remediation</b>", styles["Heading2"]))

    remediation = data.get("remediation", [])

    if not remediation:
        elements.append(Paragraph("No remediation required.", styles["Normal"]))

    for r in remediation:
        elements.append(Paragraph(
            f"{r.get('issue')} — {r.get('recommendation')} "
            f"(Priority: {r.get('priority')})",
            styles["Normal"]
        ))

    elements.append(Spacer(1, 20))

    # ---------------------------
    # FOOTER
    # ---------------------------
    elements.append(Paragraph(
        "Generated by CyberClinic AI Compliance Engine",
        styles["Italic"]
    ))

    # BUILD PDF
    doc.build(elements)

    return {
        "status": "success",
        "report_id": report_id,
        "download_url": f"/reports/download/{report_id}"
    }

# ----------------------------------
# DOWNLOAD
# ----------------------------------

@app.get("/reports/download/{report_id}")
def download_report(report_id: str):
    file_path = f"reports/{report_id}.pdf"
    return FileResponse(file_path, media_type="application/pdf")

# ----------------------------------
# HISTORY
# ----------------------------------

@app.get("/reports/history")
def get_report_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    results = db.query(AssessmentResult)\
        .filter(AssessmentResult.user_id == current_user.id)\
        .order_by(AssessmentResult.created_at.desc())\
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