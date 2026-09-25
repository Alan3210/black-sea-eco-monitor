from datetime import datetime, timezone

from backend.schemas.evidence_crosscheck import (
    EvidencePosition,
    EvidenceRecord,
)
from backend.schemas.evidence_quality import EvidenceQualityMetadata


def test_evidence_record_quality_extension():
    record = EvidenceRecord(
        source_type="station_measurement",
        provider="EEA",
        pollutant="PM10",
        value=10,
        unit="ug.m-3",
        observed_at=datetime.now(timezone.utc),
        position=EvidencePosition(
            latitude=42,
            longitude=27,
        ),
        quality=EvidenceQualityMetadata(
            freshness_seconds=60,
            temporal_alignment="exact",
            spatial_alignment="station_point",
        ),
    )

    assert record.quality.temporal_alignment == "exact"
