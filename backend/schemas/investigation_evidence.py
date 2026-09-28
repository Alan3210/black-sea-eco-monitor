from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvidenceLocation(BaseModel):
    latitude: float
    longitude: float


class CanonicalEvidenceRecord(BaseModel):
    id: str
    event_id: str
    evidence_type: str
    source: str | None = None
    timestamp: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    title: str | None = None
    location: EvidenceLocation | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict
    )


class InvestigationEvidenceBundle(BaseModel):
    event_id: str
    evidence: list[CanonicalEvidenceRecord] = Field(
        default_factory=list
    )
    candidate_sources: list[dict[str, Any]] = Field(
        default_factory=list
    )