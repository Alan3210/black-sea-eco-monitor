from sqlalchemy import Column, String, Float

from database.database import Base


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