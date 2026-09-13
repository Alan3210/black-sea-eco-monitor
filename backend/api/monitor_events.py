from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from agents.news_agent.event_store import (
    EventStore,
)


router = APIRouter()


def get_monitor_event_store():
    return EventStore()


@router.get("/")
def get_monitor_events(
    store: EventStore = Depends(
        get_monitor_event_store
    ),
):
    return store.list_event_records()


@router.get("/{event_id}")
def get_monitor_event(
    event_id: str,
    store: EventStore = Depends(
        get_monitor_event_store
    ),
):
    event = store.get_event_record(
        event_id
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return event


@router.get("/{event_id}/evidence")
def get_monitor_event_evidence(
    event_id: str,
    store: EventStore = Depends(
        get_monitor_event_store
    ),
):
    event = store.get_event_record(
        event_id
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return store.get_event_evidence_records(
        event_id
    )
