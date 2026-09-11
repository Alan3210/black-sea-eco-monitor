from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from backend.database.database import get_db

from backend.database.models import EvidenceDB


router = APIRouter()



@router.get("/{event_id}/evidence")
def get_event_evidence(
    event_id: str,
    db: Session = Depends(get_db)
):

    evidences = (
        db.query(EvidenceDB)
        .filter(
            EvidenceDB.event_id == event_id
        )
        .all()
    )


    return evidences