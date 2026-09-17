from fastapi.testclient import TestClient

from backend.api.ar_scene import get_ar_event_store
from backend.main import app


class FakeEventStore:
    def list_event_records(self):
        return [
            {
                "id": "evt_api_v04_001",
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
    app.dependency_overrides.pop(get_ar_event_store, None)


def test_ar_scene_v04_heading_contract():
    _install_ar_override()

    try:
        response = client.get(
            "/api/ar/scene",
            params={
                "observer_lat": 44.724,
                "observer_lon": 37.7691,
                "heading_deg": 0.0,
            },
        )
    finally:
        _remove_ar_override()

    assert response.status_code == 200

    data = response.json()

    assert data["contract_version"] == "0.4"
    assert data["heading_deg"] == 0.0

    incident = data["objects"][0]

    assert incident["distance_label"] == "0 m"
    assert incident["distance_tier"] == "near"
    assert incident["relative_angle_deg"] == 0.0
    assert incident["direction_hint"] == "center"


def test_ar_scene_v04_without_heading_keeps_dynamic_fields_null():
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
    incident = data["objects"][0]

    assert data["heading_deg"] is None
    assert incident["distance_label"] == "0 m"
    assert incident["distance_tier"] == "near"
    assert incident["relative_angle_deg"] is None
    assert incident["direction_hint"] is None
