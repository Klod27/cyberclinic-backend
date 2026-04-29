from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import os
import traceback
from datetime import datetime

from database import get_db
from models import Report, Organization
from auth import get_current_user

# ENGINE
from compliance_engine import run_compliance_scan

# AI + PDF
from ai_recommendations import generate_recommendations
from hipaa_pdf_report import generate_pdf

router = APIRouter()


# ----------------------------------
# PAYMENT CHECK
# ----------------------------------
def is_paid(report: Report):
    return report.is_paid


# ----------------------------------
# GENERATE REPORT
# ----------------------------------
@router.post("/reports/generate")
def generate_report(
    org_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        # Validate organization
        org = db.query(Organization).filter(
            Organization.id == org_id,
            Organization.id == user.organization_id
        ).first()

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # -------------------------
        # FILE PATH SETUP
        # -------------------------
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(BASE_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        filename = f"hipaa_report_{org_id}_{int(datetime.utcnow().timestamp())}.pdf"
        output_path = os.path.join(reports_dir, filename)

        # -------------------------
        # RUN COMPLIANCE SCAN
        # -------------------------
        scan_data = run_compliance_scan()

        findings = scan_data.get("findings", [])
        score = scan_data.get("score", 0)
        category_scores = scan_data.get("category_scores", {})

        # -------------------------
        # AI RECOMMENDATIONS
        # -------------------------
        issues = [f.get("title") or f.get("issue") for f in findings]

        ai_recommendations = generate_recommendations({
            "issues": issues
        })

        # -------------------------
        # BUILD REPORT DATA
        # -------------------------
        data = {
            "organization": org.name,
            "score": score,
            "findings": findings,
            "category_scores": category_scores,
            "ai_recommendations": ai_recommendations
        }

        # -------------------------
        # GENERATE PDF
        # -------------------------
        file_path = generate_pdf(data, output_path)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="PDF not created")

        # -------------------------
        # SAVE REPORT (LOCKED)
        # -------------------------
        report = Report(
            organization_id=org_id,
            file_path=file_path,
            is_paid=False
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        return {
            "message": "Report generated",
            "report_id": report.id
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ----------------------------------
# CHECK REPORT PAYMENT STATUS
# ----------------------------------
@router.get("/reports/status/{report_id}")
def report_status(
    report_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.organization_id == user.organization_id
    ).first()

    # ✅ SAFE RESPONSE (prevents frontend crash)
    if not report:
        return {"is_paid": False}

    return {"is_paid": report.is_paid}


# ----------------------------------
# DOWNLOAD REPORT (PAYWALL PROTECTED)
# ----------------------------------
@router.get("/reports/download/{report_id}")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.organization_id == user.organization_id
        ).first()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # 🔒 PAYWALL ENFORCED
        if not is_paid(report):
            raise HTTPException(status_code=403, detail="Payment required")

        if not os.path.exists(report.file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=report.file_path,
            media_type="application/pdf",
            filename="CyberClinic_Report.pdf"
        )

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# ----------------------------------
# LIST REPORTS
# ----------------------------------
@router.get("/reports/list")
def list_reports(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        reports = db.query(Report).filter(
            Report.organization_id == user.organization_id
        ).order_by(Report.created_at.desc()).all()

        return [
            {
                "id": r.id,
                "date": r.created_at.strftime("%Y-%m-%d"),
                "status": "Paid" if r.is_paid else "Locked"
            }
            for r in reports
        ]

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})