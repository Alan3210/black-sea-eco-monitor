from __future__ import annotations

from backend.schemas.evidence_crosscheck import (
    EvidenceRecord,
)
from backend.schemas.investigation_evidence import (
    CanonicalEvidenceRecord,
    EvidenceLocation,
)


EVIDENCE_TYPE_MAP = {
    "model_forecast": "atmospheric_model",
    "station_measurement": "ground_measurement",
    "satellite_observation": "satellite_observation",
}


def environmental_record_to_canonical(
    event_id: str,
    record: EvidenceRecord,
    record_id: str,
) -> CanonicalEvidenceRecord:
    evidence_type = EVIDENCE_TYPE_MAP.get(
        record.source_type,
        "environmental_observation",
    )

    return CanonicalEvidenceRecord(
        id=record_id,
        event_id=event_id,
        evidence_type=evidence_type,
        source=record.provider,
        timestamp=record.observed_at.isoformat(),
        title=record.pollutant,
        location=EvidenceLocation(
            latitude=record.position.latitude,
            longitude=record.position.longitude,
        ),
        metadata={
            "pollutant": record.pollutant,
            "value": record.value,
            "unit": record.unit,
            "source_type": record.source_type,
        },
        provenance={
            "source_uri": record.source_uri,
        },
    )