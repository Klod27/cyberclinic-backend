from fastapi import APIRouter
from fastapi.responses import JSONResponse
from compliance_engine import run_compliance_scan
from datetime import datetime
import traceback

router = APIRouter()

@router.get("/automation/run")
def run_scan():
    try:
        print("🚀 Running compliance scan...")

        result = run_compliance_scan()

        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )