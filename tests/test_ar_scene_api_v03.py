from fastapi.testclient import TestClient

from backend.api.ar_scene import get_ar_event_store
from backend.main import app


class FakeEventStore:
    def list_event_records(self):
        return [
            {
                "id": "evt_api_v03_001",
                "category": "wildfire",
                "location": {
                    "name": "Novorossiysk",
                    "latitude": 44.724,
                    "longitude": 37.7691,
                    "type": "city",
                    "confidence": 0.9,
                    "source": "canonical_database",
                },
                "time": {
                    "incident_time": None,
                    "detection_time": "2026-09-12T22:30:48+00:00",
                    "source_time": "2026-09-09T18:05:18+00:00",
                },
                "primary_title": "Test wildfire",
                "status": "detected",
                "severity": "medium",
                "confidence": 0.8,
                "evidence_count": 3,
            }
        ]


client = TestClient(app)


def _override_store():
    return FakeEventStore()


def _install_ar_override():
    app.dependency_overrides[get_ar_event_store] = _override_store


def _remove_ar_override():
    # Preserve unrelated overrides, especially tests/conftest.py::get_db.
    app.dependency_overrides.pop(get_ar_event_store, None)


def test_ar_scene_accepts_observer_coordinates():
    _install_ar_override()

    try:
        response = client.get(
            "/api/ar/scene",
            params={
                "observer_lat": 44.724,
                "observer_lon": 37.7691,
            },
        )
    finally:
        _remove_ar_override()

    assert response.status_code == 200

    data = response.json()

    assert data["scene_id"] == "black_sea_conference_scene_v3"
    assert data["observer"]["latitude"] == 44.724
    assert data["observer"]["longitude"] == 37.7691
    assert data["objects"][0]["distance_m"] == 0.0
    assert data["objects"][0]["bearing_deg"] == 0.0


def test_ar_scene_requires_observer_pair():
    _install_ar_override()

    try:
        response = client.get(
            "/api/ar/scene",
            params={
                "observer_lat": 44.724,
            },
        )
    finally:
        _remove_ar_override()

    assert response.status_code == 400


def test_ar_scene_distance_filter():
    _install_ar_override()

    try:
        response = client.get(
            "/api/ar/scene",
            params={
                "observer_lat": 44.724,
                "observer_lon": 37.7691,
                "max_distance_km": 1.0,
            },
        )
    finally:
        _remove_ar_override()

    assert response.status_code == 200

    data = response.json()

    object_ids = {
        obj["id"]
        for obj in data["objects"]
    }

    assert "evt_api_v03_001" in object_ids
    assert "demo_current_001" not in object_ids
    assert "demo_oil_forecast_001" not in object_ids
