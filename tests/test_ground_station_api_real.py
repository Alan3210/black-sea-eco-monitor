from backend.services.ground_station_service import get_station_observations


def test_ground_station_api_hook():
    result = get_station_observations("unknown")

    assert result["source"] == "unknown"
    assert result["status"] == "provider_not_connected"
