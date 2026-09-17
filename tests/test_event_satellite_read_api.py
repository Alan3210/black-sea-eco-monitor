import pytest
from fastapi.testclient import TestClient

from agents.news_agent.event_store import EventStore
from backend.api.monitor_events import (
    get_monitor_event_store,
)
from backend.main import app


@pytest.fixture
def linked_store(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Novorossiysk",
        primary_title="Test event",
        latitude=44.724,
        longitude=37.7691,
    )

    observation_id = (
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            platform="D",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1D_LINK_TEST_SCENE",
            acquisition_time=(
                "2026-09-17T03:31:58Z"
            ),
            derivation_level="processed",
            review_status="unreviewed",
            processing_version="0.1",
        )
    )

    created = (
        store.link_satellite_observation_to_event(
            event_id=event_id,
            satellite_observation_id=observation_id,
            relation_type="spatial_overlap",
            relation_confidence=None,
        )
    )

    assert created is True

    return store, event_id, observation_id


@pytest.fixture
def monitor_api(linked_store):
    store, event_id, observation_id = linked_store

    app.dependency_overrides[
        get_monitor_event_store
    ] = lambda: store

    client = TestClient(app)

    try:
        yield (
            client,
            store,
            event_id,
            observation_id,
        )
    finally:
        app.dependency_overrides.pop(
            get_monitor_event_store,
            None,
        )


def test_store_returns_linked_satellite_observation(
    linked_store,
):
    store, event_id, observation_id = linked_store

    records = (
        store.get_event_satellite_observations(
            event_id
        )
    )

    assert len(records) == 1

    record = records[0]

    assert record["relation_type"] == (
        "spatial_overlap"
    )
    assert record["relation_confidence"] is None
    assert record["created_at"] is not None

    observation = record["observation"]

    assert observation["id"] == observation_id
    assert observation["information_type"] == (
        "satellite_observation"
    )
    assert observation["observation_type"] == (
        "sar_scene"
    )
    assert observation["sensor"] == "Sentinel-1"
    assert observation["dataset_id"] == (
        "COPERNICUS/S1_GRD"
    )


def test_store_returns_empty_list_when_event_has_no_links(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Gelendzhik",
        primary_title="Unlinked event",
    )

    assert (
        store.get_event_satellite_observations(
            event_id
        )
        == []
    )


def test_monitor_event_satellite_endpoint_returns_200(
    monitor_api,
):
    (
        client,
        _store,
        event_id,
        observation_id,
    ) = monitor_api

    response = client.get(
        f"/monitor/events/{event_id}/"
        "satellite-observations"
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["relation_type"] == (
        "spatial_overlap"
    )
    assert payload[0]["observation"]["id"] == (
        observation_id
    )


def test_monitor_event_satellite_endpoint_returns_empty_list(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Gelendzhik",
        primary_title="Unlinked event",
    )

    app.dependency_overrides[
        get_monitor_event_store
    ] = lambda: store

    client = TestClient(app)

    try:
        response = client.get(
            f"/monitor/events/{event_id}/"
            "satellite-observations"
        )
    finally:
        app.dependency_overrides.pop(
            get_monitor_event_store,
            None,
        )

    assert response.status_code == 200
    assert response.json() == []


def test_monitor_event_satellite_endpoint_missing_event_returns_404(
    monitor_api,
):
    client, _store, _event_id, _observation_id = (
        monitor_api
    )

    response = client.get(
        "/monitor/events/evt_missing/"
        "satellite-observations"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Event not found"
    }


def test_event_satellite_read_side_does_not_mutate_records(
    monitor_api,
):
    client, store, event_id, observation_id = monitor_api

    before_event = store.get_event_record(
        event_id
    )
    before_observation = (
        store.get_satellite_observation(
            observation_id
        )
    )

    response = client.get(
        f"/monitor/events/{event_id}/"
        "satellite-observations"
    )

    after_event = store.get_event_record(
        event_id
    )
    after_observation = (
        store.get_satellite_observation(
            observation_id
        )
    )

    assert response.status_code == 200
    assert after_event == before_event
    assert after_observation == before_observation
