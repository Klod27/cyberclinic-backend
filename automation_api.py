from fastapi import APIRouter
from fastapi.responses import JSONResponse
from compliance_engine import run_compliance_scan
import traceback

router = APIRouter()

@router.get("/automation/run")
def run_scan():
    try:
        result = run_compliance_scan()

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )