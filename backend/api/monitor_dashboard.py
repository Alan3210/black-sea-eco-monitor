from fastapi import (
    APIRouter,
    Depends,
)

from agents.news_agent.event_store import (
    EventStore,
)

from backend.services.operator_dashboard import (
    build_operator_dashboard,
)


router = APIRouter()


def get_dashboard_event_store():
    return EventStore()


@router.get("/events")
def get_operator_dashboard_events(
    status: str | None = None,
    category: str | None = None,
    has_coordinates: bool | None = None,
    store: EventStore = Depends(
        get_dashboard_event_store
    ),
):
    return build_operator_dashboard(
        store,
        status=status,
        category=category,
        has_coordinates=has_coordinates,
    )
