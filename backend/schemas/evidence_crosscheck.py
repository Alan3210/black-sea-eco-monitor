from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from backend.schemas.evidence_quality import EvidenceQualityMetadata


EvidenceSourceType = Literal[
    "model_forecast",
    "satellite_observation",
    "station_measurement",
]


class EvidencePosition(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class EvidenceRecord(BaseModel):
    source_type: EvidenceSourceType
    provider: str
    pollutant: str
    value: float
    unit: str
    observed_at: datetime
    position: EvidencePosition
    source_uri: str | None = None
    quality: EvidenceQualityMetadata | None = None


class EvidenceCrosscheck(BaseModel):
    position: EvidencePosition
    observed_at: datetime
    sources: list[EvidenceRecord] = Field(default_factory=list)
