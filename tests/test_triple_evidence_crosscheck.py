from datetime import datetime, timezone

from backend.services.triple_evidence_crosscheck_service import (
    build_triple_evidence_crosscheck,
)
from backend.schemas.station import (
    StationObservation,
    StationProvenance,
)


def test_triple_crosscheck():
    now = datetime.now(timezone.utc)

    station = StationObservation(
        station_id="S1",
        latitude=42.0,
        longitude=27.0,
        pollutant="NO2",
        value=10.0,
        unit="ug.m-3",
        observed_at=now,
        provenance=StationProvenance(
            provider="EEA",
            retrieved_at=now,
        ),
    )

    result = build_triple_evidence_crosscheck(
        station,
        {
            "provider": "CAMS",
            "pollutant": "NO2",
            "value": 11.0,
            "unit": "ug.m-3",
            "observed_at": now,
            "latitude": 42.0,
            "longitude": 27.0,
        },
        {
            "provider": "Sentinel-5P",
            "pollutant": "NO2",
            "value": 12.0,
            "unit": "mol/m2",
            "observed_at": now,
            "latitude": 42.0,
            "longitude": 27.0,
        },
    )

    assert len(result.sources) == 3
    assert result.sources[0].source_type == "station_measurement"
    assert result.sources[1].source_type == "model_forecast"
    assert result.sources[2].source_type == "satellite_observation"
