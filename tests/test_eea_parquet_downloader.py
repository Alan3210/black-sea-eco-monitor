from backend.services.eea_parquet_downloader import EEAParquetDownloader


class FakeResponse:
    content = b"parquet-test"

    def raise_for_status(self):
        pass


class FakeSession:
    def get(self, *args, **kwargs):
        return FakeResponse()


def test_downloader_cache(tmp_path):
    loader = EEAParquetDownloader(
        cache_dir=tmp_path,
        session=FakeSession(),
    )

    result = loader.download_file(
        "https://example.com/test.parquet"
    )

    assert result.exists()
    assert result.name == "test.parquet"
