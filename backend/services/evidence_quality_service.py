from backend.schemas.evidence_quality import EvidenceQualityMetadata


def build_evidence_quality_metadata(
    *,
    freshness_seconds=None,
    temporal_alignment="unknown",
    spatial_alignment="unknown",
    quality_flags=None,
):
    return EvidenceQualityMetadata(
        freshness_seconds=freshness_seconds,
        temporal_alignment=temporal_alignment,
        spatial_alignment=spatial_alignment,
        quality_flags=quality_flags or [],
    )
