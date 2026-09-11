from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.database.models import EventDB

from backend.models.event import EnvironmentalEvent

from backend.services import event_service

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

    return event_service.get_all_events(db)



@router.post("/")
def create_event(
    event: EnvironmentalEvent,
    db: Session = Depends(get_db)
):

    created = event_service.create_event(
        db,
        event
    )

    return {
        "status": "created",
        "event": created
    }



@router.get("/{event_id}")
def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):

    return event_service.get_event_by_id(
        db,
        event_id
    )