from fastapi import APIRouter

from backend.services.evidence_crosscheck_api_service import (
    get_evidence_crosscheck,
)

router = APIRouter(prefix="/air", tags=["air"])


@router.get("/evidence-crosscheck")
def evidence_crosscheck():
    return get_evidence_crosscheck()
