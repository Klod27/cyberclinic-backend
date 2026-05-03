from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from compliance_engine import run_compliance_scan
from datetime import datetime
import traceback
import logging

router = APIRouter()

# ----------------------------------
# LOGGING (IMPORTANT FOR RENDER DEBUG)
# ----------------------------------
logger = logging.getLogger(__name__)

# ----------------------------------
# AUTOMATION ROUTE
# ----------------------------------
@router.get("/automation/run")
async def run_scan(request: Request):
    try:
        logger.info("🚀 /automation/run endpoint triggered")

        # 🔍 Log request origin (VERY IMPORTANT for debugging CORS / Vercel)
        origin = request.headers.get("origin")
        logger.info(f"🌐 Request origin: {origin}")

        # 🔍 Log headers (helps debug auth / blocking issues)
        logger.info(f"📡 Headers: {dict(request.headers)}")

        # ----------------------------------
        # RUN CORE ENGINE (NO FEATURE REMOVED)
        # ----------------------------------
        result = run_compliance_scan()

        # ----------------------------------
        # SAFE RESPONSE (JSON SERIALIZABLE)
        # ----------------------------------
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    except Exception as e:
        # 🔥 FULL STACK TRACE FOR RENDER LOGS
        traceback.print_exc()
        logger.error(f"❌ Automation error: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# ----------------------------------
# 🔥 OPTIONAL: PREFLIGHT SUPPORT (VERY IMPORTANT FOR VERCEL)
# ----------------------------------
@router.options("/automation/run")
async def options_run_scan():
    """
    Handles CORS preflight requests from browsers.
    Without this, Vercel frontend may silently fail.
    """
    return JSONResponse(
        status_code=200,
        content={"message": "OK"}
    )