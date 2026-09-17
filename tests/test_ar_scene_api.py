from fastapi.testclient import TestClient

from backend.api.ar_scene import get_ar_event_store
from backend.main import app


class FakeEventStore:
    def list_event_records(self):
        return [
            {
                "id": "evt_api_test_001",
                "category": "wildfire",
                "location": {
                    "name": "Utrish Reserve",
                    "latitude": 44.7605,
                    "longitude": 37.3854,
                    "type": "protected_area",
                    "confidence": 0.8,
                    "source": "canonical_database",
                },
                "time": {
                    "incident_time": None,
                    "detection_time": "2026-09-12T22:30:48+00:00",
                    "source_time": "2026-09-09T18:05:18+00:00",
                },
                "primary_title": "Test wildfire",
                "status": "contained",
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
    # Remove only the override owned by this test module.
    # Do NOT clear the whole mapping: tests/conftest.py keeps the test DB
    # override for get_db in the same global dictionary.
    app.dependency_overrides.pop(get_ar_event_store, None)


def test_ar_scene_route_is_reachable():
    _install_ar_override()

    try:
        response = client.get("/api/ar/scene")
    finally:
        _remove_ar_override()

    assert response.status_code == 200


def test_ar_scene_endpoint_returns_eventstore_scene():
    _install_ar_override()

    try:
        response = client.get("/api/ar/scene")
    finally:
        _remove_ar_override()

    assert response.status_code == 200

    data = response.json()

    assert data["scene_id"] == "black_sea_conference_scene_v3"
    assert len(data["objects"]) == 3

    incident = data["objects"][0]

    assert incident["id"] == "evt_api_test_001"
    assert incident["type"] == "incident"
    assert incident["category"] == "wildfire"
    assert incident["location_name"] == "Utrish Reserve"
    assert incident["coordinate_source"] == "canonical_database"

    object_types = {
        obj["type"]
        for obj in data["objects"]
    }

    assert object_types == {
        "incident",
        "current",
        "oil_forecast",
    }


def test_ar_scene_endpoint_contains_unity_friendly_fields():
    _install_ar_override()

    try:
        response = client.get("/api/ar/scene")
    finally:
        _remove_ar_override()

    assert response.status_code == 200

    data = response.json()

    assert "generated_at" in data
    assert "center" in data

    first_object = data["objects"][0]

    assert "id" in first_object
    assert "type" in first_object
    assert "position" in first_object
    assert "visual" in first_object
    assert "title" in first_object
