from __future__ import annotations

from backend.schemas.evidence_crosscheck import (
    EvidenceRecord,
    EvidencePosition,
)


def sentinel_to_evidence_record(
    sentinel_observation: dict,
) -> EvidenceRecord:
    return EvidenceRecord(
        source_type="satellite_observation",
        provider=sentinel_observation.get(
            "provider",
            "Sentinel-5P",
        ),
        pollutant=sentinel_observation["pollutant"],
        value=float(sentinel_observation["value"]),
        unit=sentinel_observation["unit"],
        observed_at=sentinel_observation["observed_at"],
        position=EvidencePosition(
            latitude=sentinel_observation["latitude"],
            longitude=sentinel_observation["longitude"],
        ),
        source_uri=sentinel_observation.get("source_uri"),
    )
