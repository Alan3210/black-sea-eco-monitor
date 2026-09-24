from backend.services.ground_station_service import (
    get_station_observations,
)


def test_station_service_adapter():
    result = get_station_observations()

    assert result["source"] == "eea"
    assert result["status"] == "provider_connected"
    assert isinstance(result["stations"], list)
