from fastapi import APIRouter

from backend.services.evidence_timeline_service import (
    build_evidence_timeline,
)

router = APIRouter(prefix="/air", tags=["air"])


@router.get("/evidence-timeline")
def evidence_timeline(
    pollutant: str = "PM10",
):
    return build_evidence_timeline(pollutant)
