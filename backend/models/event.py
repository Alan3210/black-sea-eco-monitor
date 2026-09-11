from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from backend.models.evidence import Evidence


class EventCategory(str, Enum):
    oil_spill = "oil_spill"
    wildfire = "wildfire"
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
        ge=0,
        le=1
    )

    sources: List[str] = []

    evidences: List[Evidence] = []

    description: Optional[str] = None