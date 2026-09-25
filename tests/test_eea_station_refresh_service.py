from backend.services.eea_station_refresh_service import (
    refresh_eea_station_observations,
)

class FakeResponse:
    text = "ParquetFileUrl\nhttps://example.com/test.parquet"
    content = b"test"

    def raise_for_status(self):
        pass

class FakeSession:
    def post(self, *args, **kwargs):
        return FakeResponse()

    def get(self, *args, **kwargs):
        return FakeResponse()


def test_refresh_service():
    result = refresh_eea_station_observations(
        session=FakeSession()
    )

    assert result["status"] == "success"
    assert result["files_discovered"] == 1
