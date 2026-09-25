from datetime import datetime, timezone

from backend.services.sentinel_evidence_adapter import (
    sentinel_to_evidence_record,
)


def test_sentinel_adapter():
    result = sentinel_to_evidence_record(
        {
            "provider": "Sentinel-5P",
            "pollutant": "NO2",
            "value": 12.5,
            "unit": "mol/m2",
            "observed_at": datetime.now(timezone.utc),
            "latitude": 42.0,
            "longitude": 27.0,
        }
    )

    assert result.provider == "Sentinel-5P"
    assert result.source_type == "satellite_observation"
