from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.impact import (
    get_impact_event_store,
    router,
)


class FakeEventStore:
    def list_event_records(self):
        return [
            {
                "id": "evt_001",
                "location": {
                    "name": "Novorossiysk",
                    "latitude": 44.724,
                    "longitude": 37.7691,
                    "type": "city",
                    "confidence": 0.9,
                    "source": "canonical_database",
                },
            },
            {
                "id": "evt_002",
                "location": {
                    "name": "Utrish Reserve",
                    "latitude": 44.7605,
                    "longitude": 37.3854,
                    "type": "protected_area",
                    "confidence": 0.8,
                    "source": "canonical_database",
                },
            },
        ]


def _fake_store():
    return FakeEventStore()


app = FastAPI()
app.include_router(router)

app.dependency_overrides[
    get_impact_event_store
] = _fake_store

client = TestClient(app)


def test_impact_targets_endpoint():
    response = client.get(
        "/impact/targets"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    names = {
        item["name"]
        for item in data
    }

    assert names == {
        "Novorossiysk",
        "Utrish Reserve",
    }


def test_impact_drift_endpoint():
    response = client.post(
        "/impact/drift",
        json={
            "proximity_threshold_km": 1.0,
            "forecast": {
                "model": "OpenDrift OceanDrift",
                "scope": (
                    "passive_surface_tracer_current_only"
                ),
                "horizons": [
                    {
                        "hours": 6,
                        "time": (
                            "2026-09-17T06:00:00+00:00"
                        ),
                        "points": [
                            [37.7691, 44.7240]
                        ],
                    }
                ],
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["analysis_type"]
        == "drift_proximity_screening_v0.1"
    )
    assert data["target_count"] == 2
    assert data["potentially_affected_count"] == 1

    first = data["assessments"][0]

    assert first["target"]["name"] == "Novorossiysk"
    assert first["potentially_affected"] is True
    assert first["first_exposure_hours"] == 6
