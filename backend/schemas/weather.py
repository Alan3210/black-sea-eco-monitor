from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


WeatherDataKind = Literal[
    "forecast",
    "analysis",
    "reanalysis",
    "observation",
]


class WeatherUnits(BaseModel):
    wind_components: str = "m/s"
    wind_speed: str = "m/s"
    wind_direction: str = "degrees_from_north"
    precipitation_rate: str = "mm/h"
    precipitation_accumulation: str = "mm"


class WeatherProvenance(BaseModel):
    provider: str
    model: str
    product: str
    data_kind: WeatherDataKind
    forecast_reference_time: datetime | None = None
    valid_time: datetime
    retrieved_at: datetime
    source_uri: str | None = None
    fallback_used: bool = False
    quality_flags: list[str] = Field(default_factory=list)


class WeatherPoint(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)

    wind_u_10m_ms: float
    wind_v_10m_ms: float
    wind_speed_10m_ms: float = Field(ge=0.0)
    wind_from_direction_deg: float = Field(ge=0.0, lt=360.0)

    precipitation_rate_mm_h: float | None = Field(default=None, ge=0.0)
    precipitation_accumulation_mm: float | None = Field(default=None, ge=0.0)
    precipitation_interval_start: datetime | None = None
    precipitation_interval_end: datetime | None = None

    provenance: WeatherProvenance
    units: WeatherUnits = Field(default_factory=WeatherUnits)
