from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.models.evidence import Evidence


class EventCategory(str, Enum):
    oil_spill = "oil_spill"
    wildfire = "wildfire"
    industrial_fire = "industrial_fire"
    water_pollution = "water_pollution"
    algae_bloom = "algae_bloom"
    marine_animal_death = "marine_animal_death"
    chemical_release = "chemical_release"
    storm_damage = "storm_damage"


class EventSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Location(BaseModel):
    latitude: float
    longitude: float


class EnvironmentalEvent(BaseModel):
    id: str

    type: str = "environmental_event"

    category: EventCategory

    status: str = "detected"

    location: Location

    timestamp: str

    severity: EventSeverity

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    sources: List[str] = Field(
        default_factory=list
    )

    evidences: List[Evidence] = Field(
        default_factory=list
    )

    description: Optional[str] = None