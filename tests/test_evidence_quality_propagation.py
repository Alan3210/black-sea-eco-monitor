from datetime import datetime, timezone

from backend.schemas.evidence_crosscheck import (
    EvidenceCrosscheck,
    EvidencePosition,
    EvidenceRecord,
)
from backend.schemas.evidence_quality import EvidenceQualityMetadata


def test_quality_propagates_inside_crosscheck():
    quality = EvidenceQualityMetadata(
        freshness_seconds=60,
        temporal_alignment="exact",
        spatial_alignment="station_point",
    )

    record = EvidenceRecord(
        source_type="station_measurement",
        provider="EEA",
        pollutant="PM10",
        value=10,
        unit="ug.m-3",
        observed_at=datetime.now(timezone.utc),
        position=EvidencePosition(latitude=42, longitude=27),
        quality=quality,
    )

    crosscheck = EvidenceCrosscheck(
        position=record.position,
        observed_at=record.observed_at,
        sources=[record],
    )

    assert crosscheck.sources[0].quality.spatial_alignment == "station_point"
