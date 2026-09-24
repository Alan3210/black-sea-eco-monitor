from datetime import datetime, timezone

from backend.services.eea_station_field import (
    build_station_observations,
    normalize_eea_observation,
)


def test_empty_payload_returns_empty_list():
    assert build_station_observations({"stations": []}) == []


def test_normalize_eea_observation():
    item = normalize_eea_observation(
        {
            "station_id": "EEA_BG_TEST",
            "country": "BG",
            "latitude": 43.2,
            "longitude": 27.9,
            "pollutant": "PM10",
            "value": 12.5,
            "unit": "ug/m3",
            "observed_at": datetime.now(timezone.utc),
        }
    )

    assert item.station_id == "EEA_BG_TEST"
    assert item.provenance.provider == "EEA"
    assert item.validation_status == "unverified"
