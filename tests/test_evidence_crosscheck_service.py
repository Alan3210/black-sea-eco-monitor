from datetime import datetime, timezone

from backend.services.evidence_crosscheck_service import (
    build_station_cams_crosscheck,
)
from backend.schemas.station import (
    StationObservation,
    StationProvenance,
)


def test_station_cams_crosscheck():
    station = StationObservation(
        station_id="S1",
        latitude=42.0,
        longitude=27.0,
        pollutant="PM10",
        value=70.0,
        unit="ug.m-3",
        observed_at=datetime.now(timezone.utc),
        provenance=StationProvenance(
            provider="EEA",
            retrieved_at=datetime.now(timezone.utc),
        ),
    )

    result = build_station_cams_crosscheck(
        station,
        {
            "provider": "CAMS",
            "pollutant": "PM10",
            "value": 65.0,
            "unit": "ug.m-3",
            "observed_at": datetime.now(timezone.utc),
            "latitude": 42.0,
            "longitude": 27.0,
        },
    )

    assert len(result.sources) == 2
    assert result.sources[0].source_type == "station_measurement"
    assert result.sources[1].source_type == "model_forecast"
