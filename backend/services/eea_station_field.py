from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from backend.schemas.station import StationObservation, StationProvenance


def normalize_eea_observation(
    raw: dict,
    *,
    retrieved_at: datetime | None = None,
) -> StationObservation:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)

    return StationObservation(
        station_id=raw["station_id"],
        station_name=raw.get("station_name"),
        country=raw.get("country"),
        latitude=raw["latitude"],
        longitude=raw["longitude"],
        classification=None,
        pollutant=raw["pollutant"],
        value=raw["value"],
        unit=raw["unit"],
        observed_at=raw["observed_at"],
        validation_status="unverified",
        provenance=StationProvenance(
            provider="EEA",
            network=raw.get("network", "EEA AQ e-Reporting"),
            dataset="E2a",
            retrieved_at=retrieved_at,
            source_uri=raw.get("source_uri"),
        ),
    )


def build_station_observations(payload: dict) -> list[StationObservation]:
    stations = payload.get("stations", [])
    return [
        normalize_eea_observation(item)
        for item in stations
    ]
