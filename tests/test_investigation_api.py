import pytest
from fastapi.testclient import TestClient

from agents.news_agent.event_store import EventStore
from backend.api.monitor_events import (
    get_monitor_event_store,
)
from backend.main import app


@pytest.fixture
def investigation_api(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="oil_spill",
        location_name="Novorossiysk",
        primary_title="Investigation API test",
        latitude=44.724,
        longitude=37.7691,
    )

    store.add_evidence(
        event_id=event_id,
        source="Test Source",
        title="Oil spill report",
        url="https://example.com/report",
        published_at=(
            "2026-09-28T10:15:00+00:00"
        ),
        confidence=0.8,
        reason="Initial source report",
    )

    observation_id = (
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1_API_TEST_SCENE",
            acquisition_time=(
                "2026-09-28T10:30:00Z"
            ),
            confidence=0.9,
            processing_version="0.1",
        )
    )

    store.link_satellite_observation_to_event(
        event_id=event_id,
        satellite_observation_id=observation_id,
        relation_type="spatial_overlap",
        relation_confidence=0.75,
    )

    app.dependency_overrides[
        get_monitor_event_store
    ] = lambda: store

    with TestClient(app) as client:
        yield client, event_id, observation_id

    app.dependency_overrides.pop(
        get_monitor_event_store,
        None,
    )


def test_investigation_api_returns_canonical_evidence(
    investigation_api,
):
    client, event_id, observation_id = (
        investigation_api
    )

    response = client.get(
        f"/monitor/events/{event_id}/investigation"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event_id"] == event_id
    assert payload["candidate_sources"] == []
    assert len(payload["evidence"]) == 2

    assert payload["evidence"][0][
        "evidence_type"
    ] == "source_report"

    satellite = payload["evidence"][1]

    assert satellite["id"] == observation_id
    assert satellite[
        "evidence_type"
    ] == "satellite_observation"
    assert satellite["source"] == "Sentinel-1"
    assert satellite["confidence"] == 0.9
    assert satellite["metadata"][
        "relation_confidence"
    ] == 0.75


def test_investigation_api_missing_event_returns_404(
    investigation_api,
):
    client, *_ = investigation_api

    response = client.get(
        "/monitor/events/evt_missing/investigation"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Event not found"
    }