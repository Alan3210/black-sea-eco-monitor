from __future__ import annotations

from backend.schemas.evidence_crosscheck import (
    EvidenceRecord,
    EvidencePosition,
)
from backend.schemas.station import StationObservation


def cams_to_evidence_record(cams_observation: dict) -> EvidenceRecord:
    return EvidenceRecord(
        source_type="model_forecast",
        provider=cams_observation.get("provider", "CAMS"),
        pollutant=cams_observation["pollutant"],
        value=float(cams_observation["value"]),
        unit=cams_observation["unit"],
        observed_at=cams_observation["observed_at"],
        position=EvidencePosition(
            latitude=cams_observation["latitude"],
            longitude=cams_observation["longitude"],
        ),
        source_uri=cams_observation.get("source_uri"),
    )


def station_to_evidence_record(
    station: StationObservation,
) -> EvidenceRecord:
    return EvidenceRecord(
        source_type="station_measurement",
        provider=station.provenance.provider,
        pollutant=station.pollutant,
        value=station.value,
        unit=station.unit,
        observed_at=station.observed_at,
        position=EvidencePosition(
            latitude=station.latitude,
            longitude=station.longitude,
        ),
        source_uri=station.provenance.source_uri,
    )
