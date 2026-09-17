from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ImpactPosition(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class ImpactTarget(BaseModel):
    id: str
    name: str
    type: str | None = None
    position: ImpactPosition
    location_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    coordinate_source: str | None = None


class DriftImpactRequest(BaseModel):
    forecast: dict[str, Any]

    proximity_threshold_km: float = Field(
        default=5.0,
        gt=0.0,
        le=100.0,
        description=(
            "Screening radius around each target. "
            "This is a proximity threshold, not a claim of confirmed impact."
        ),
    )


class ImpactAssessment(BaseModel):
    target: ImpactTarget

    potentially_affected: bool

    first_exposure_hours: int | None = None
    first_exposure_time: str | None = None

    closest_horizon_hours: int | None = None
    minimum_distance_km: float | None = None

    affected_horizons: list[int] = Field(
        default_factory=list,
    )


class DriftImpactResponse(BaseModel):
    analysis_type: str = "drift_proximity_screening_v0.1"

    model_source: str | None = None
    forecast_scope: str | None = None

    screening_method: str = "particle_proximity"
    proximity_threshold_km: float

    target_source: str = "event_store_known_locations"

    target_count: int
    potentially_affected_count: int

    assessments: list[ImpactAssessment] = Field(
        default_factory=list,
    )
