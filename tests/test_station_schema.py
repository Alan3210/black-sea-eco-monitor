from datetime import datetime, timezone

from backend.schemas.station import (
    StationObservation,
    StationProvenance,
)


def test_station_observation_schema():
    item = StationObservation(
        station_id="EEA_TEST",
        country="BG",
        latitude=43.2,
        longitude=27.9,
        pollutant="PM2.5",
        value=12.4,
        unit="µg/m³",
        observed_at=datetime.now(timezone.utc),
        provenance=StationProvenance(
            provider="EEA",
            network="EEA AQ e-Reporting",
            dataset="E2a",
            retrieved_at=datetime.now(timezone.utc),
        ),
    )

    assert item.station_id == "EEA_TEST"
    assert item.pollutant == "PM2.5"
    assert item.provenance.provider == "EEA"


def test_station_coordinates_validation():
    try:
        StationObservation(
            station_id="BAD",
            latitude=100,
            longitude=0,
            pollutant="PM10",
            value=1,
            unit="µg/m³",
            observed_at=datetime.now(timezone.utc),
            provenance=StationProvenance(
                provider="TEST",
                retrieved_at=datetime.now(timezone.utc),
            ),
        )
    except Exception:
        return

    raise AssertionError("Invalid latitude must fail")
