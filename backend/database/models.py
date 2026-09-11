from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship


from backend.database.database import Base


class EventDB(Base):

    __tablename__ = "events"

    id = Column(
        String,
        primary_key=True,
        index=True
    )

    category = Column(
        String,
        nullable=False
    )

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    timestamp = Column(
        String,
        nullable=False
    )

    severity = Column(
        String,
        nullable=False
    )

    confidence = Column(
        Float,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    evidences = relationship(
    "EvidenceDB",
    backref="event"
    )

class SourceDB(Base):

    __tablename__ = "sources"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    type = Column(
        String,
        nullable=False
    )

    name = Column(
        String,
        nullable=False
    )

    url = Column(
        String,
        nullable=True
    )

    reliability = Column(
        Float,
        default=0.5
    )

    evidences = relationship(
    "EvidenceDB",
    backref="source"
    )

class EvidenceDB(Base):

    __tablename__ = "evidences"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    event_id = Column(
        String,
        ForeignKey("events.id")
    )

    source_id = Column(
        Integer,
        ForeignKey("sources.id")
    )

    type = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=False
    )

    confidence = Column(
        Float,
        nullable=False
    )