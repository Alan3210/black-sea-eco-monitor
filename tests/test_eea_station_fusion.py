from datetime import datetime, timezone

from backend.services.eea_station_fusion import (
    fuse_eea_station_observation,
    normalize_samplingpoint_id,
)


def test_normalize_samplingpoint_id():
    assert normalize_samplingpoint_id(
        "BG/SPO-BG001"
    ) == "SPO-BG001"


def test_fusion_creates_observation():
    result = fuse_eea_station_observation(
        {
            "AQStationName": "Test Station",
            "Country": "BG",
            "Latitude": 42.0,
            "Longitude": 27.0,
            "AirQualityStationArea": "urban",
            "AirQualityStationType": "background",
            "AirQualityNetwork": "NET-BG",
        },
        {
            "samplingpoint": "BG/SPO-BG001",
            "pollutant_code": 5,
            "value": 10.5,
            "unit": "ug.m-3",
            "observed_at": datetime.now(timezone.utc),
            "verification": 1,
        },
    )

    assert result.station_id == "SPO-BG001"
    assert result.provenance.provider == "EEA"
