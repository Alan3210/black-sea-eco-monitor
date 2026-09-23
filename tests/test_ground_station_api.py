from backend.services.ground_station_service import get_station_sources

def test_station_sources_contains_eea():
    ids = [x["id"] for x in get_station_sources()]
    assert "eea" in ids
