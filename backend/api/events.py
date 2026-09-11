from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import EventDB

from models.event import EnvironmentalEvent


router = APIRouter()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()



@router.get("/")
def get_events(
    db: Session = Depends(get_db)
):

    events = db.query(EventDB).all()

    return events



@router.post("/")
def create_event(
    event: EnvironmentalEvent,
    db: Session = Depends(get_db)
):

    db_event = EventDB(

        id=event.id,

        category=event.category.value,

        latitude=event.location.latitude,

        longitude=event.location.longitude,

        timestamp=event.timestamp,

        severity=event.severity.value,

        confidence=event.confidence,

        description=event.description
    )


    db.add(db_event)

    db.commit()

    db.refresh(db_event)


    return {
        "status": "created",
        "event": db_event
    }



@router.get("/{event_id}")
def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):

    event = (
        db.query(EventDB)
        .filter(EventDB.id == event_id)
        .first()
    )


    if event:
        return event


    return {
        "error": "Event not found"
    }