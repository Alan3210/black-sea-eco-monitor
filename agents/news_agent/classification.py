from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from backend.models.event import EventCategory


class NewsClassificationType(str, Enum):
    incident = "incident"
    reported = "reported"
    follow_up = "follow_up"
    background = "background"
    forecast = "forecast"
    clear = "clear"
    noise = "noise"


class NewsClassification(BaseModel):

    classification: NewsClassificationType

    category: Optional[EventCategory] = None

    location_name: Optional[str] = None

    is_black_sea_region: Optional[bool] = None

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    is_new_event: Optional[bool] = None

    event_date: Optional[str] = None

    reason: str