from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from backend.services.eea_station_runtime_provider import (
    get_eea_station_observations,
)
from backend.services.eea_measurement_parser import (
    parse_eea_measurements,
)


def load_metadata_rows(path="data/cache/air/eea-metadata/stations.json"):
    file = Path(path)
    if not file.exists():
        return []

    return json.loads(file.read_text(encoding="utf-8"))


def load_measurements(path):
    return parse_eea_measurements(path)


def load_eea_station_observations(
    metadata_path,
    parquet_path,
):
    metadata_rows = load_metadata_rows(metadata_path)
    measurements = load_measurements(parquet_path)

    return get_eea_station_observations(
        metadata_rows,
        measurements,
    )
