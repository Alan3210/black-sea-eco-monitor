from backend.services.evidence_quality_integration import (
    station_evidence_with_quality,
    cams_evidence_with_quality,
    sentinel_evidence_with_quality,
)


def test_station_quality_integration():
    result = station_evidence_with_quality({})
    assert result["quality"].spatial_alignment == "station_point"


def test_cams_quality_integration():
    result = cams_evidence_with_quality({})
    assert result["quality"].spatial_alignment == "grid_cell"


def test_sentinel_quality_integration():
    result = sentinel_evidence_with_quality({})
    assert result["quality"].spatial_alignment == "satellite_pixel"
