from sqlalchemy.orm import Session

from backend.database.models import (
    EventDB,
    EvidenceDB,
    SourceDB
)

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

    db.flush()


    for evidence in event.evidences:

        source_db = None


        if evidence.source:

            source_db = SourceDB(

                type=evidence.source.type,

                name=evidence.source.name,

                url=evidence.source.url,

                reliability=evidence.source.reliability
            )

            db.add(source_db)

            db.flush()


        evidence_db = EvidenceDB(

            event_id=db_event.id,

            source_id=(
                source_db.id
                if source_db
                else None
            ),

            type=evidence.type,

            description=evidence.description,

            confidence=evidence.confidence
        )


        db.add(evidence_db)


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