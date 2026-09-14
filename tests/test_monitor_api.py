import pytest

from fastapi.testclient import TestClient

from agents.news_agent.event_store import (
    EventStore,
)

from backend.api.monitor_events import (
    get_monitor_event_store,
)

from backend.main import app


@pytest.fixture
def monitor_api_client(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Test wildfire",
        status="active",
        severity="medium",
        confidence=0.8,
        latitude=44.7240,
        longitude=37.7691,
        location_type="city",
        location_confidence=0.72,
        coordinate_source="canonical_database",
        incident_time="2026-09-13T09:30:00Z",
        detection_time="2026-09-13T10:00:00Z",
        source_time="2026-09-13T10:15:00Z",
    )

    store.add_evidence(
        event_id=event_id,
        source="Test Source",
        title="Test wildfire report",
        url="https://example.com/test",
        published_at=(
            "2026-09-13T10:15:00+00:00"
        ),
        confidence=0.8,
        reason="Test evidence.",
    )

    app.dependency_overrides[
        get_monitor_event_store
    ] = lambda: store

    with TestClient(app) as client:
        yield client, event_id

    app.dependency_overrides.pop(
        get_monitor_event_store,
        None,
    )


def test_monitor_events_list(
    monitor_api_client,
):
    client, event_id = (
        monitor_api_client
    )

    response = client.get(
        "/monitor/events/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == event_id
    assert (
        data[0]["location"]["latitude"]
        == 44.7240
    )
    assert (
        data[0]["evidence_count"]
        == 1
    )


def test_monitor_event_by_id(
    monitor_api_client,
):
    client, event_id = (
        monitor_api_client
    )

    response = client.get(
        f"/monitor/events/{event_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == event_id
    assert data["status"] == "active"
    assert (
        data["location"]["name"]
        == "Novorossiysk"
    )


def test_monitor_api_exposes_location_quality(
    monitor_api_client,
):
    client, event_id = (
        monitor_api_client
    )

    response = client.get(
        f"/monitor/events/{event_id}"
    )

    assert response.status_code == 200

    location = response.json()["location"]

    assert location == {
        "name": "Novorossiysk",
        "latitude": 44.724,
        "longitude": 37.7691,
        "type": "city",
        "confidence": 0.72,
        "source": "canonical_database",
    }


def test_monitor_api_exposes_event_time_metadata(
    monitor_api_client,
):
    client, event_id = (
        monitor_api_client
    )

    response = client.get(
        f"/monitor/events/{event_id}"
    )

    assert response.status_code == 200

    assert response.json()["time"] == {
        "incident_time": "2026-09-13T09:30:00+00:00",
        "detection_time": "2026-09-13T10:00:00+00:00",
        "source_time": "2026-09-13T10:15:00+00:00",
    }


def test_monitor_event_evidence(
    monitor_api_client,
):
    client, event_id = (
        monitor_api_client
    )

    response = client.get(
        (
            f"/monitor/events/"
            f"{event_id}/evidence"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert (
        data[0]["source"]
        == "Test Source"
    )
    assert (
        data[0]["url"]
        == "https://example.com/test"
    )


def test_monitor_event_not_found(
    monitor_api_client,
):
    client, _event_id = (
        monitor_api_client
    )

    response = client.get(
        "/monitor/events/evt_missing"
    )

    assert response.status_code == 404
