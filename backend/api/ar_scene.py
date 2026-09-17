from fastapi import APIRouter, Depends, HTTPException, Query

from agents.news_agent.event_store import EventStore

from backend.schemas.ar import ARPosition, ARScene
from backend.services.ar_scene_builder import build_ar_scene


router = APIRouter(
    prefix="/api/ar",
    tags=["ar"],
)


def get_ar_event_store() -> EventStore:
    return EventStore()


@router.get(
    "/scene",
    response_model=ARScene,
)
def get_ar_scene(
    observer_lat: float | None = Query(
        default=None,
        ge=-90.0,
        le=90.0,
        description=(
            "Observer latitude. Supply together with observer_lon. "
            "If omitted, the conference demo observer is used."
        ),
    ),
    observer_lon: float | None = Query(
        default=None,
        ge=-180.0,
        le=180.0,
        description=(
            "Observer longitude. Supply together with observer_lat. "
            "If omitted, the conference demo observer is used."
        ),
    ),
    max_distance_km: float | None = Query(
        default=None,
        gt=0.0,
        le=500.0,
        description=(
            "Optional maximum distance from observer. "
            "Objects farther away are omitted."
        ),
    ),
    store: EventStore = Depends(get_ar_event_store),
) -> ARScene:
    """
    Return a normalized scene for Unity/mobile AR clients.

    v0.3 adds an observer position plus precomputed distance/bearing for
    each object. Current/OpenOil remain lightweight cached/demo objects.
    """
    if (observer_lat is None) != (observer_lon is None):
        raise HTTPException(
            status_code=400,
            detail=(
                "observer_lat and observer_lon must be supplied together"
            ),
        )

    observer = None

    if observer_lat is not None and observer_lon is not None:
        observer = ARPosition(
            latitude=observer_lat,
            longitude=observer_lon,
        )

    return build_ar_scene(
        store.list_event_records(),
        observer=observer,
        max_distance_km=max_distance_km,
    )
