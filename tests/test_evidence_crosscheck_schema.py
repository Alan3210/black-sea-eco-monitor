from datetime import datetime, timezone

from backend.schemas.evidence_crosscheck import (
    EvidenceCrosscheck,
    EvidencePosition,
    EvidenceRecord,
)


def test_evidence_crosscheck_contract():
    item = EvidenceRecord(
        source_type="station_measurement",
        provider="EEA",
        pollutant="PM10",
        value=20.0,
        unit="ug.m-3",
        observed_at=datetime.now(timezone.utc),
        position=EvidencePosition(
            latitude=42.0,
            longitude=27.0,
        ),
    )

    result = EvidenceCrosscheck(
        position=item.position,
        observed_at=item.observed_at,
        sources=[item],
    )

    assert result.sources[0].provider == "EEA"
    assert result.sources[0].source_type == "station_measurement"
