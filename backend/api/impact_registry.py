from fastapi import APIRouter
from backend.services.impact_registry import get_impact_registry_targets

router = APIRouter(prefix="/impact", tags=["impact"])

@router.get("/registry")
def registry():
    targets = get_impact_registry_targets()
    return {
        "registry": "impact_registry_v01",
        "count": len(targets),
        "targets": [t.model_dump() for t in targets],
    }
