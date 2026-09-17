from fastapi import APIRouter, Depends

from agents.news_agent.event_store import EventStore

from backend.schemas.impact import (
    DriftImpactRequest,
    DriftImpactResponse,
    ImpactTarget,
)
from backend.services.impact_service import (
    analyze_drift_impact,
    build_targets_from_event_records,
)


router = APIRouter(
    prefix="/impact",
    tags=["impact"],
)


def get_impact_event_store() -> EventStore:
    return EventStore()


@router.get(
    "/targets",
    response_model=list[ImpactTarget],
)
def get_impact_targets(
    store: EventStore = Depends(
        get_impact_event_store
    ),
) -> list[ImpactTarget]:
    """
    Return geolocated places currently known to the canonical EventStore.

    v0.1 uses these as screening targets. This is not yet a complete
    coastline/protected-area/settlement registry.
    """
    return build_targets_from_event_records(
        store.list_event_records()
    )


@router.post(
    "/drift",
    response_model=DriftImpactResponse,
)
def analyze_drift_forecast(
    request: DriftImpactRequest,
    store: EventStore = Depends(
        get_impact_event_store
    ),
) -> DriftImpactResponse:
    """
    Screen an existing OceanDrift forecast against known locations.

    Important: this endpoint does NOT start OpenDrift, OpenOil, Copernicus,
    or ECMWF downloads. The forecast is supplied by the caller.
    """
    targets = build_targets_from_event_records(
        store.list_event_records()
    )

    return analyze_drift_impact(
        forecast=request.forecast,
        targets=targets,
        proximity_threshold_km=(
            request.proximity_threshold_km
        ),
    )
