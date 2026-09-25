from fastapi import APIRouter

router = APIRouter(prefix="/air", tags=["air"])


@router.get("/dashboard-status")
def dashboard_status():
    return {
        "status": "ready",
        "modules": [
            "summary",
            "timeline",
            "quality",
            "evidence_crosscheck",
        ],
    }
