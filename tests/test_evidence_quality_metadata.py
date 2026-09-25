from backend.services.evidence_quality_service import (
    build_evidence_quality_metadata,
)


def test_evidence_quality_metadata_contract():
    result = build_evidence_quality_metadata(
        freshness_seconds=300,
        temporal_alignment="exact",
        spatial_alignment="station_point",
    )

    assert result.freshness_seconds == 300
    assert result.temporal_alignment == "exact"
    assert result.spatial_alignment == "station_point"
