import pytest
from fastapi.testclient import TestClient

from agents.news_agent.event_store import EventStore
from backend.api.monitor_events import (
    get_monitor_event_store,
)
from backend.main import app
from backend.services.monitor_context import (
    build_monitor_event_context,
)


@pytest.fixture
def context_store(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Novorossiysk",
        primary_title="Context test event",
        latitude=44.724,
        longitude=37.7691,
    )

    observation_id = store.create_satellite_observation(
        observation_type="sar_scene",
        sensor="Sentinel-1",
        dataset_id="COPERNICUS/S1_GRD",
        source_image_id="S1D_CONTEXT_TEST",
        acquisition_time="2026-09-17T03:31:58Z",
    )

    store.link_satellite_observation_to_event(
        event_id=event_id,
        satellite_observation_id=observation_id,
        relation_type="spatial_overlap",
    )

    return store, event_id, observation_id


@pytest.fixture
def context_api(context_store):
    store, event_id, observation_id = (
        context_store
    )

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


def test_service_returns_event_evidence_and_satellite(
    context_store,
):
    store, event_id, observation_id = (
        context_store
    )

    context = build_monitor_event_context(
        store,
        event_id,
    )

    assert context is not None
    assert context["event"]["id"] == event_id
    assert context["evidence"] == []
    assert context["satellite"]["count"] == 1
    assert context["satellite"][
        "observations"
    ][0]["observation"]["id"] == observation_id


def test_service_builds_coordinate_ready_drift_link(
    context_store,
):
    store, event_id, _ = context_store

    context = build_monitor_event_context(
        store,
        event_id,
    )

    drift = context[
        "capabilities"
    ]["ocean_drift"]

    assert context[
        "readiness"
    ]["event_has_coordinates"] is True

    assert drift["available"] is True
    assert drift["starts_model"] is True
    assert drift["href"] == (
        "/ocean/drift/"
        "?lon=37.7691&lat=44.724"
    )


def test_service_marks_drift_unavailable_without_coordinates(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Unknown",
        primary_title="No coordinate event",
    )

    context = build_monitor_event_context(
        store,
        event_id,
    )

    assert context[
        "readiness"
    ]["event_has_coordinates"] is False

    drift = context[
        "capabilities"
    ]["ocean_drift"]

    assert drift["available"] is False
    assert drift["href"] is None


def test_service_exposes_exact_capability_contracts(
    context_store,
):
    store, event_id, _ = context_store

    context = build_monitor_event_context(
        store,
        event_id,
    )

    capabilities = context["capabilities"]

    assert capabilities["ocean_currents"] == {
        "available": True,
        "method": "GET",
        "href": "/ocean/currents/",
    }

    assert capabilities[
        "impact_screening"
    ]["href"] == "/impact/drift"

    assert capabilities[
        "impact_screening"
    ]["targets_href"] == "/impact/targets"

    assert capabilities[
        "impact_screening"
    ]["requires"] == [
        "drift_forecast_payload"
    ]

    assert capabilities[
        "impact_screening"
    ]["starts_model"] is False

    assert capabilities[
        "ar_scene"
    ]["href"] == "/api/ar/scene"

    assert capabilities[
        "ar_scene"
    ]["observer_location_is_user_position"] is True


def test_service_exposes_canonical_links(
    context_store,
):
    store, event_id, _ = context_store

    context = build_monitor_event_context(
        store,
        event_id,
    )

    assert context["links"] == {
        "event": (
            f"/monitor/events/{event_id}"
        ),
        "evidence": (
            f"/monitor/events/{event_id}/evidence"
        ),
        "satellite_observations": (
            f"/monitor/events/{event_id}/"
            "satellite-observations"
        ),
        "satellite_candidates_geojson": (
            "/satellite/observations/"
            "candidates.geojson"
        ),
    }


def test_api_returns_200_and_context(
    context_api,
):
    client, _store, event_id, _ = (
        context_api
    )

    response = client.get(
        f"/monitor/events/{event_id}/context"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["event"]["id"] == event_id
    assert payload["satellite"]["count"] == 1
    assert payload[
        "capabilities"
    ]["ocean_drift"]["available"] is True


def test_api_missing_event_returns_404(
    context_api,
):
    client, *_ = context_api

    response = client.get(
        "/monitor/events/evt_missing/context"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Event not found"
    }


def test_context_read_side_does_not_mutate_event(
    context_api,
):
    client, store, event_id, _ = (
        context_api
    )

    before = store.get_event_record(
        event_id
    )

    response = client.get(
        f"/monitor/events/{event_id}/context"
    )

    after = store.get_event_record(
        event_id
    )

    assert response.status_code == 200
    assert after == before
