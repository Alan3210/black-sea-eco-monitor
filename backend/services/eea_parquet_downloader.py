from pathlib import Path
from urllib.parse import urlparse
import requests


class EEAParquetDownloader:

    def __init__(
        self,
        cache_dir="data/cache/air/eea-stations/parquet",
        session=None,
        timeout=120,
    ):
        self.cache_dir = Path(cache_dir)
        self.session = session or requests.Session()
        self.timeout = timeout

    def _target_path(self, url):
        name = Path(urlparse(url).path).name
        return self.cache_dir / name

    def download_file(self, url):
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        target = self._target_path(url)

        if target.exists():
            return target

        response = self.session.get(
            url,
            timeout=self.timeout,
        )
        response.raise_for_status()

        target.write_bytes(response.content)

        return target

    def download_urls(self, urls):
        return [
            self.download_file(url)
            for url in urls
        ]
