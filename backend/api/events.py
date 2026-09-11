from fastapi import APIRouter

from models.event import EnvironmentalEvent


router = APIRouter()


events = []


@router.get("/")
def get_events():

    return events



@router.post("/")
def create_event(event: EnvironmentalEvent):

    events.append(event)

    return {
        "status": "created",
        "event": event
    }



@router.get("/{event_id}")
def get_event(event_id: str):

    for event in events:

        if event.id == event_id:
            return event


    return {
        "error": "Event not found"
    }