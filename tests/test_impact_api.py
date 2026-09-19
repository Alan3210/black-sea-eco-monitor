from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.impact import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_impact_targets_endpoint_uses_registry():
    response = client.get("/impact/targets")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 25

    names = {
        item["name"]
        for item in data
    }

    assert "Novorossiysk" in names
    assert "Novorossiysk Port" in names
    assert "Utrish Reserve" in names
    assert "Anapa Coastal Zone" in names

    types = {
        item["type"]
        for item in data
    }

    assert {
        "settlement",
        "port",
        "protected_area",
        "coastal_zone",
    }.issubset(types)

    assert all(
        item["coordinate_source"]
        == "impact_registry_v01"
        for item in data
    )


def test_impact_drift_endpoint_uses_registry_targets():
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
                            [37.769, 44.724]
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

    assert data["target_count"] == 25
    assert data["potentially_affected_count"] >= 1

    novorossiysk = next(
        item
        for item in data["assessments"]
        if item["target"]["name"] == "Novorossiysk"
    )

    assert novorossiysk["potentially_affected"] is True
    assert novorossiysk["first_exposure_hours"] == 6
    assert novorossiysk["minimum_distance_km"] == 0.0
