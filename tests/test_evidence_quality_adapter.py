from backend.services.evidence_quality_adapter import (
    station_quality_metadata,
    cams_quality_metadata,
    sentinel_quality_metadata,
)


def test_station_quality_adapter():
    result = station_quality_metadata(60)

    assert result.temporal_alignment == "exact"
    assert result.spatial_alignment == "station_point"


def test_cams_quality_adapter():
    result = cams_quality_metadata(300)

    assert result.spatial_alignment == "grid_cell"


def test_sentinel_quality_adapter():
    result = sentinel_quality_metadata(600)

    assert result.spatial_alignment == "satellite_pixel"
