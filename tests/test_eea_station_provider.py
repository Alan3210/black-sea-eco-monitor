from backend.services.eea_station_provider import (
    EEAStationProvider,
    discover_eea_parquet_urls,
)


def test_provider_exists():
    assert EEAStationProvider is not None


class FakeResponse:
    text = "ParquetFileUrl\nhttps://example.com/a.parquet"

    def raise_for_status(self):
        pass


class FakeSession:
    def post(self, *args, **kwargs):
        return FakeResponse()


def test_url_discovery():
    assert discover_eea_parquet_urls(
        session=FakeSession()
    ) == ["https://example.com/a.parquet"]
