from fastapi import APIRouter

from backend.services.evidence_summary_service import (
    build_evidence_summary,
)

router = APIRouter(prefix="/air", tags=["air"])


@router.get("/evidence-summary")
def evidence_summary():
    return build_evidence_summary()
