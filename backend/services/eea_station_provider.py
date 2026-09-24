from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import requests


DEFAULT_EEA_API_BASE = (
    "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
)

EEA_URLS_ENDPOINT = DEFAULT_EEA_API_BASE + "/ParquetFile/urls"


class EEAStationError(RuntimeError):
    pass


@dataclass(frozen=True)
class EEAStationArtifact:
    path: Path
    metadata_path: Path
    cache_hit: bool
    metadata: Mapping[str, Any]


class EEAStationProvider:
    def __init__(
        self,
        *,
        api_base: str = DEFAULT_EEA_API_BASE,
        cache_dir: str | Path = "data/cache/air/eea-stations",
        session=None,
        timeout: float = 120.0,
    ):
        self.api_base = api_base
        self.cache_dir = Path(cache_dir)
        self.session = session
        self.timeout = timeout

    def fetch_stations(
        self,
        *,
        countries=("BG", "RO"),
        pollutants=None,
        force=False,
    ) -> EEAStationArtifact:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "provider": "EEA",
            "dataset": "E2a",
            "countries": list(countries),
            "pollutants": pollutants or [],
        }

        path = self.cache_dir / "stations.json"
        metadata_path = self.cache_dir / "metadata.json"

        if path.exists() and metadata_path.exists() and not force:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            return EEAStationArtifact(
                path=path,
                metadata_path=metadata_path,
                cache_hit=True,
                metadata=metadata,
            )

        path.write_text(
            json.dumps({"stations": [], "request": payload}, indent=2),
            encoding="utf-8",
        )

        metadata = {
            "provider": "EEA",
            "dataset": "E2a",
            "kind": "station_measurement",
            "verification": "unverified",
        }

        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

        return EEAStationArtifact(
            path=path,
            metadata_path=metadata_path,
            cache_hit=False,
            metadata=metadata,
        )


def discover_eea_parquet_urls(
    countries=("BG", "RO"),
    pollutants=None,
    session=None,
):
    session = session or requests.Session()

    payload = {
        "countries": list(countries),
        "cities": [],
        "pollutants": pollutants or [],
        "dataset": 1,
        "aggregationType": "hour",
    }

    response = session.post(
        EEA_URLS_ENDPOINT,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    return [
        line.strip()
        for line in response.text.splitlines()
        if line.strip() and "ParquetFileUrl" not in line
    ]
