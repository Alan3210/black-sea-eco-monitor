from datetime import datetime, timezone

from backend.services.eea_station_runtime_provider import (
    get_eea_station_observations,
)


def test_runtime_provider():
    result = get_eea_station_observations(
        [
            {
                "AssessmentMethodId": "SPO-BG001",
                "AQStationName": "Test",
                "Country": "BG",
                "Latitude": 42.0,
                "Longitude": 27.0,
                "AirQualityNetwork": "NET-BG",
                "AirQualityStationArea": "urban",
                "AirQualityStationType": "background",
            }
        ],
        [
            {
                "samplingpoint": "BG/SPO-BG001",
                "pollutant_code": 5,
                "value": 10,
                "unit": "ug.m-3",
                "observed_at": datetime.now(timezone.utc),
                "verification": 1,
            }
        ],
    )

    assert len(result) == 1
    assert result[0].country == "BG"
