from __future__ import annotations

from datetime import datetime, timezone

from backend.schemas.station import (
    StationObservation,
    StationClassification,
    StationProvenance,
)


def normalize_samplingpoint_id(value: str) -> str:
    if value.startswith("BG/") or "/" in value[:3]:
        return value.split("/", 1)[-1]
    return value


def fuse_eea_station_observation(
    metadata: dict,
    measurement: dict,
) -> StationObservation:

    station_id = normalize_samplingpoint_id(
        measurement["samplingpoint"]
    )

    return StationObservation(
        station_id=station_id,
        station_name=metadata.get("AQStationName"),
        country=metadata.get("Country"),
        latitude=metadata["Latitude"],
        longitude=metadata["Longitude"],
        classification=StationClassification(
            area=metadata.get(
                "AirQualityStationArea",
                "unknown",
            ),
            station_type=metadata.get(
                "AirQualityStationType",
                "unknown",
            ),
        ),
        pollutant=str(
            measurement["pollutant_code"]
        ),
        value=float(measurement["value"]),
        unit=measurement["unit"],
        observed_at=measurement["observed_at"],
        validation_status=str(
            measurement.get(
                "verification",
                "unknown",
            )
        ),
        provenance=StationProvenance(
            provider="EEA",
            network=metadata.get(
                "AirQualityNetwork"
            ),
            dataset="E2a",
            retrieved_at=datetime.now(timezone.utc),
        ),
    )
