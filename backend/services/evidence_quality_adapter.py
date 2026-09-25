from backend.schemas.evidence_quality import EvidenceQualityMetadata


def attach_evidence_quality(
    evidence,
    quality: EvidenceQualityMetadata,
):
    return {
        "evidence": evidence,
        "quality": quality,
    }


def station_quality_metadata(
    freshness_seconds=None,
):
    return EvidenceQualityMetadata(
        freshness_seconds=freshness_seconds,
        temporal_alignment="exact",
        spatial_alignment="station_point",
    )


def cams_quality_metadata(
    freshness_seconds=None,
):
    return EvidenceQualityMetadata(
        freshness_seconds=freshness_seconds,
        temporal_alignment="model_time",
        spatial_alignment="grid_cell",
    )


def sentinel_quality_metadata(
    freshness_seconds=None,
):
    return EvidenceQualityMetadata(
        freshness_seconds=freshness_seconds,
        temporal_alignment="observation_time",
        spatial_alignment="satellite_pixel",
    )
