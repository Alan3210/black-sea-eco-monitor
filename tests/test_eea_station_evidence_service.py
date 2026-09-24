from datetime import datetime, timezone

from backend.services.eea_station_evidence_service import (
    build_eea_station_observations,
)


def test_real_style_fusion():
    metadata = [
        {
            "AssessmentMethodId": "SPO-BG0071A_00005_100",
            "AQStationName": "Test Station",
            "Country": "BG",
            "Latitude": 42.0,
            "Longitude": 27.0,
            "AirQualityStationArea": "urban",
            "AirQualityStationType": "background",
            "AirQualityNetwork": "NET-BG",
        }
    ]

    measurements = [
        {
            "samplingpoint": "BG/SPO-BG0071A_00005_100",
            "pollutant_code": 5,
            "value": 73.72,
            "unit": "ug.m-3",
            "observed_at": datetime.now(timezone.utc),
            "verification": 1,
        }
    ]

    result = build_eea_station_observations(
        metadata,
        measurements,
    )

    assert len(result) == 1
    assert result[0].country == "BG"
    assert result[0].provenance.provider == "EEA"
