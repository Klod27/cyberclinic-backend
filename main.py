from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
import logging

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

# AI
from ai_recommendations import generate_recommendations

# Database
from database import engine, get_db, Base
import models
from models import AssessmentResult

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
# SECURITY
# ----------------------------------
security = HTTPBearer()

# ----------------------------------
# APP
# ----------------------------------
app = FastAPI(
    title="CyberClinic Compliance API",
    version="2.0.0"
)

# ----------------------------------
# 🔥 CORS FIX (CRITICAL)
# ----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ FIX: allow all origins (unblocks Vercel immediately)
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
    return {
        "message": "CyberClinic API running",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }

# ----------------------------------
# HEALTH CHECK
# ----------------------------------
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ----------------------------------
# AUTH TEST
# ----------------------------------
@app.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "message": "Authenticated successfully"
    }

# ----------------------------------
# PAYMENT ROUTES
# ----------------------------------
@app.get("/success", response_class=HTMLResponse)
def payment_success():
    return "<h1>Payment Successful</h1>"

@app.get("/cancel", response_class=HTMLResponse)
def payment_cancel():
    return "<h1>Payment Cancelled</h1>"

# ----------------------------------
# ANALYTICS
# ----------------------------------
@app.get("/analytics/trend/{organization_id}")
def get_trend(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        results = db.query(AssessmentResult)\
            .filter(AssessmentResult.organization_id == organization_id)\
            .order_by(AssessmentResult.created_at)\
            .all()

        return [
            {
                "date": r.created_at.strftime("%Y-%m-%d"),
                "score": r.overall_score,
                "risk": r.risk_level
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Analytics failed")

# ----------------------------------
# AI RECOMMENDATIONS
# ----------------------------------
@app.post("/ai-recommendations")
async def ai_recommendations(data: dict):
    try:
        issues = [f.get("issue", "") for f in data.get("findings", [])]

        recommendations = generate_recommendations({
            "issues": issues
        })

        return {
            "status": "success",
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"AI error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))