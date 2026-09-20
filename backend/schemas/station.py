from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


StationArea = Literal[
    "urban",
    "suburban",
    "rural",
    "unknown",
]


StationType = Literal[
    "traffic",
    "industrial",
    "background",
    "unknown",
]


class StationClassification(BaseModel):
    area: StationArea = "unknown"
    station_type: StationType = "unknown"


class StationProvenance(BaseModel):
    provider: str
    network: str | None = None
    dataset: str | None = None
    retrieved_at: datetime
    source_uri: str | None = None


class StationObservation(BaseModel):
    station_id: str

    station_name: str | None = None
    country: str | None = None

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)

    classification: StationClassification | None = None

    pollutant: str
    value: float
    unit: str

    observed_at: datetime

    validation_status: str = "unknown"

    provenance: StationProvenance
