from backend.services.eea_station_provider import EEAStationProvider


def test_fetch_stations_creates_artifact(tmp_path):
    provider = EEAStationProvider(cache_dir=tmp_path)

    first = provider.fetch_stations()

    assert first.cache_hit is False
    assert first.path.exists()
    assert first.metadata["provider"] == "EEA"


def test_cache_hit(tmp_path):
    provider = EEAStationProvider(cache_dir=tmp_path)

    provider.fetch_stations()
    second = provider.fetch_stations()

    assert second.cache_hit is True
