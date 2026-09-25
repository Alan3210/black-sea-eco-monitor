from backend.schemas.evidence_quality import EvidenceQualityMetadata


def attach_quality_to_evidence(
    evidence: dict,
    quality: EvidenceQualityMetadata,
):
    result = dict(evidence)
    result["quality"] = quality
    return result


def station_evidence_with_quality(evidence: dict):
    return attach_quality_to_evidence(
        evidence,
        EvidenceQualityMetadata(
            temporal_alignment="exact",
            spatial_alignment="station_point",
        ),
    )


def cams_evidence_with_quality(evidence: dict):
    return attach_quality_to_evidence(
        evidence,
        EvidenceQualityMetadata(
            temporal_alignment="model_time",
            spatial_alignment="grid_cell",
        ),
    )


def sentinel_evidence_with_quality(evidence: dict):
    return attach_quality_to_evidence(
        evidence,
        EvidenceQualityMetadata(
            temporal_alignment="observation_time",
            spatial_alignment="satellite_pixel",
        ),
    )
