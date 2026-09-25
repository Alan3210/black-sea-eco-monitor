from pydantic import BaseModel, Field


class EvidenceQualityMetadata(BaseModel):
    freshness_seconds: float | None = Field(default=None, ge=0)

    temporal_alignment: str = "unknown"
    spatial_alignment: str = "unknown"

    quality_flags: list[str] = Field(default_factory=list)
