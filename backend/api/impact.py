from fastapi import APIRouter, Depends



from backend.schemas.impact import (
    DriftImpactRequest,
    DriftImpactResponse,
    ImpactTarget,
)

from backend.services.impact_service import (
    analyze_drift_impact,
)

from backend.services.impact_registry import (
    get_impact_registry_targets,
)

router = APIRouter(
    prefix="/impact",
    tags=["impact"],
)


@router.get(
    "/targets",
    response_model=list[ImpactTarget],
)
def get_impact_targets() -> list[ImpactTarget]:

    return get_impact_registry_targets()


@router.post(
    "/drift",
    response_model=DriftImpactResponse,
)
def analyze_drift_forecast(
    request: DriftImpactRequest,
) -> DriftImpactResponse:

    targets = get_impact_registry_targets()

    return analyze_drift_impact(
        forecast=request.forecast,
        targets=targets,
        proximity_threshold_km=(
            request.proximity_threshold_km
        ),
    )
