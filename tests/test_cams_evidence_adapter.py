from datetime import datetime, timezone

from backend.services.cams_evidence_adapter import (
    cams_to_evidence_record,
)


def test_cams_adapter():
    result = cams_to_evidence_record(
        {
            "provider": "CAMS",
            "pollutant": "PM10",
            "value": 50,
            "unit": "ug.m-3",
            "observed_at": datetime.now(timezone.utc),
            "latitude": 42.0,
            "longitude": 27.0,
        }
    )

    assert result.provider == "CAMS"
    assert result.source_type == "model_forecast"
