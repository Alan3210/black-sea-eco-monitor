from backend.services.eea_station_provider import discover_eea_parquet_urls

class FakeResponse:
    text = "ParquetFileUrl\nhttps://example.com/a.parquet"

    def raise_for_status(self):
        pass

class FakeSession:
    def post(self, *args, **kwargs):
        return FakeResponse()

def test_url_discovery():
    result = discover_eea_parquet_urls(session=FakeSession())

    assert result == ["https://example.com/a.parquet"]
