import pytest
from fastapi.testclient import TestClient

from agents.news_agent.event_store import EventStore
from backend.api.monitor_dashboard import (
    get_dashboard_event_store,
)
from backend.main import app
from backend.services.operator_dashboard import (
    build_operator_dashboard,
)


@pytest.fixture
def dashboard_store(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    ready_event_id = store.create_event(
        category="industrial_fire",
        location_name="Novorossiysk",
        primary_title="Raw source title",
        status="detected",
        severity="medium",
        confidence=0.8,
        latitude=44.724,
        longitude=37.7691,
        source_time="2026-09-09T03:24:19Z",
    )

    unready_event_id = store.create_event(
        category="wildfire",
        location_name="Unknown",
        primary_title="No coordinate event",
        status="contained",
        severity="medium",
        confidence=0.7,
    )

    observation_id = (
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1D_DASHBOARD_TEST",
            acquisition_time="2026-09-17T03:31:58Z",
        )
    )

    store.link_satellite_observation_to_event(
        event_id=ready_event_id,
        satellite_observation_id=observation_id,
        relation_type="spatial_overlap",
    )

    return (
        store,
        ready_event_id,
        unready_event_id,
    )


@pytest.fixture
def dashboard_api(dashboard_store):
    store, ready_id, unready_id = (
        dashboard_store
    )

    app.dependency_overrides[
        get_dashboard_event_store
    ] = lambda: store

    client = TestClient(app)

    try:
        yield (
            client,
            store,
            ready_id,
            unready_id,
        )
    finally:
        app.dependency_overrides.pop(
            get_dashboard_event_store,
            None,
        )


def test_service_builds_operator_rows(
    dashboard_store,
):
    store, ready_id, _ = (
        dashboard_store
    )

    payload = build_operator_dashboard(
        store
    )

    assert payload["count"] == 2

    row = next(
        item
        for item in payload["items"]
        if item["id"] == ready_id
    )

    assert row["display_label"] == (
        "Novorossiysk · industrial_fire"
    )
    assert row["primary_title"] == (
        "Raw source title"
    )
    assert row["evidence_count"] == 0
    assert row["satellite_count"] == 1
    assert row["event_time"] == (
        "2026-09-09T03:24:19+00:00"
    )


def test_ready_event_exposes_workflow_readiness(
    dashboard_store,
):
    store, ready_id, _ = (
        dashboard_store
    )

    payload = build_operator_dashboard(
        store
    )

    row = next(
        item
        for item in payload["items"]
        if item["id"] == ready_id
    )

    assert row["readiness"] == {
        "has_coordinates": True,
        "ocean_drift": True,
        "impact_after_drift": True,
        "ar_scene": True,
    }


def test_event_without_coordinates_is_not_drift_ready(
    dashboard_store,
):
    store, _, unready_id = (
        dashboard_store
    )

    payload = build_operator_dashboard(
        store
    )

    row = next(
        item
        for item in payload["items"]
        if item["id"] == unready_id
    )

    assert row["readiness"][
        "has_coordinates"
    ] is False
    assert row["readiness"][
        "ocean_drift"
    ] is False
    assert row["readiness"][
        "impact_after_drift"
    ] is False


def test_service_filters_by_status_category_and_coordinates(
    dashboard_store,
):
    store, ready_id, _ = (
        dashboard_store
    )

    payload = build_operator_dashboard(
        store,
        status="detected",
        category="industrial_fire",
        has_coordinates=True,
    )

    assert payload["count"] == 1
    assert payload["items"][0]["id"] == ready_id


def test_service_exposes_context_link(
    dashboard_store,
):
    store, ready_id, _ = (
        dashboard_store
    )

    payload = build_operator_dashboard(
        store
    )

    row = next(
        item
        for item in payload["items"]
        if item["id"] == ready_id
    )

    assert row["links"]["context"] == (
        f"/monitor/events/{ready_id}/context"
    )


def test_api_returns_dashboard(
    dashboard_api,
):
    client, _store, ready_id, _ = (
        dashboard_api
    )

    response = client.get(
        "/monitor/dashboard/events"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 2
    assert any(
        item["id"] == ready_id
        for item in payload["items"]
    )


def test_api_filters_dashboard(
    dashboard_api,
):
    client, _store, ready_id, _ = (
        dashboard_api
    )

    response = client.get(
        "/monitor/dashboard/events",
        params={
            "status": "detected",
            "has_coordinates": True,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 1
    assert payload["items"][0]["id"] == ready_id


def test_dashboard_read_side_does_not_mutate_events(
    dashboard_api,
):
    client, store, ready_id, _ = (
        dashboard_api
    )

    before = store.get_event_record(
        ready_id
    )

    response = client.get(
        "/monitor/dashboard/events"
    )

    after = store.get_event_record(
        ready_id
    )

    assert response.status_code == 200
    assert after == before
