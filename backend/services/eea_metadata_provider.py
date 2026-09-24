from pathlib import Path
import json
import requests

AQVIEWER_URL = "https://discomap.eea.europa.eu/App/AQViewer/data"
AQVIEWER_FQN = "Airquality_Dissem.b2g.measurements"

class EEAMetadataError(RuntimeError):
    pass

class EEAMetadataProvider:
    def __init__(self, cache_dir="data/cache/air/eea-metadata", session=None):
        self.cache_dir = Path(cache_dir)
        self.session = session or requests.Session()

    def fetch_station_metadata(self, force=False):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache = self.cache_dir / "stations.json"

        if cache.exists() and not force:
            return json.loads(cache.read_text(encoding="utf-8"))

        body = {
            "Page": 0,
            "SortBy": None,
            "SortAscending": True,
            "RequestFilter": {}
        }

        r = self.session.post(
            AQVIEWER_URL,
            params={"fqn": AQVIEWER_FQN},
            json=body,
            timeout=120,
        )

        if r.status_code != 200:
            raise EEAMetadataError(r.text)

        rows = r.json().get("Rows", [])

        cache.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        return rows
