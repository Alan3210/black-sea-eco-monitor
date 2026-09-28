from datetime import datetime, timezone

from backend.schemas.evidence_crosscheck import (
    EvidencePosition,
    EvidenceRecord,
)
from backend.services.environmental_evidence_adapter import (
    environmental_record_to_canonical,
)


def test_converts_cams_record_to_canonical_evidence():
    record = EvidenceRecord(
        source_type="model_forecast",
        provider="CAMS",
        pollutant="PM10",
        value=42.5,
        unit="ug/m3",
        observed_at=datetime(
            2026,
            9,
            28,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        position=EvidencePosition(
            latitude=44.72,
            longitude=37.45,
        ),
        source_uri="cams://test",
    )

    result = environmental_record_to_canonical(
        event_id="evt_123",
        record=record,
        record_id="cams_1",
    )

    assert result.event_id == "evt_123"
    assert result.evidence_type == "atmospheric_model"
    assert result.source == "CAMS"
    assert result.confidence is None

    assert result.metadata == {
        "pollutant": "PM10",
        "value": 42.5,
        "unit": "ug/m3",
        "source_type": "model_forecast",
    }

    assert result.location.latitude == 44.72
    assert result.location.longitude == 37.45

    assert result.provenance["source_uri"] == (
        "cams://test"
    )


def test_converts_station_record_to_ground_evidence():
    record = EvidenceRecord(
        source_type="station_measurement",
        provider="EEA",
        pollutant="NO2",
        value=18.0,
        unit="ug/m3",
        observed_at=datetime(
            2026,
            9,
            28,
            13,
            0,
            tzinfo=timezone.utc,
        ),
        position=EvidencePosition(
            latitude=44.70,
            longitude=37.50,
        ),
        source_uri="eea://station/test",
    )

    result = environmental_record_to_canonical(
        event_id="evt_123",
        record=record,
        record_id="eea_1",
    )

    assert result.evidence_type == (
        "ground_measurement"
    )

    assert result.source == "EEA"
    assert result.title == "NO2"
    assert result.confidence is None