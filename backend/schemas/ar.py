from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ARObjectType = Literal[
    "incident",
    "current",
    "drift_forecast",
    "oil_forecast",
    "station",
]

ARPriority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

ARDirectionHint = Literal[
    "left",
    "center",
    "right",
]

ARDistanceTier = Literal[
    "near",
    "medium",
    "far",
]


class ARPosition(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class ARVisual(BaseModel):
    icon: str
    priority: ARPriority = "medium"


class ARObject(BaseModel):
    """
    Stable, Unity-friendly representation of one object in an AR scene.
    """

    id: str
    type: ARObjectType
    category: str | None = None

    position: ARPosition
    visual: ARVisual

    title: str

    # Common provenance / state
    source: str | None = None
    observed_at: str | None = None
    status: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    # Location quality / provenance
    location_name: str | None = None
    location_type: str | None = None
    location_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    coordinate_source: str | None = None

    # Explicit event-time semantics
    incident_time: str | None = None
    detection_time: str | None = None
    source_time: str | None = None
    evidence_count: int | None = Field(default=None, ge=0)

    # Observer-relative geo fields
    distance_m: float | None = Field(default=None, ge=0.0)
    bearing_deg: float | None = Field(default=None, ge=0.0, lt=360.0)

    # HUD-ready display fields
    distance_label: str | None = None
    distance_tier: ARDistanceTier | None = None
    relative_angle_deg: float | None = Field(default=None, ge=-180.0, le=180.0)
    direction_hint: ARDirectionHint | None = None

    # Current-vector fields
    speed_m_s: float | None = Field(default=None, ge=0.0)
    direction_deg: float | None = Field(default=None, ge=0.0, lt=360.0)

    # Forecast fields
    forecast_hours: int | None = Field(default=None, ge=0)
    particle_count: int | None = Field(default=None, ge=0)
    stranded_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    terminal_state: str | None = None


class ARScene(BaseModel):
    contract_version: str = "0.4"
    scene_id: str
    generated_at: str

    center: ARPosition
    observer: ARPosition | None = None

    # Heading used for snapshot HUD calculations.
    # Unity may recompute relative angle locally at frame rate.
    heading_deg: float | None = Field(default=None, ge=0.0, lt=360.0)

    objects: list[ARObject] = Field(default_factory=list)
