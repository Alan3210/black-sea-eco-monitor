from sqlalchemy.orm import Session

from backend.database.models import EventDB
from backend.models.event import EnvironmentalEvent



def create_event(
    db: Session,
    event: EnvironmentalEvent
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

    return db_event



def get_all_events(
    db: Session
):

    return (
        db.query(EventDB)
        .all()
    )



def get_event_by_id(
    db: Session,
    event_id: str
):

    return (
        db.query(EventDB)
        .filter(
            EventDB.id == event_id
        )
        .first()
    )