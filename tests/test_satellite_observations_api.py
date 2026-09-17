import pytest
from fastapi.testclient import TestClient

from agents.news_agent.event_store import EventStore
from backend.api.satellite_observations import (
    get_satellite_observation_store,
)
from backend.main import app


@pytest.fixture
def satellite_api(tmp_path):
    store = EventStore(tmp_path / "events.db")

    app.dependency_overrides[
        get_satellite_observation_store
    ] = lambda: store

    client = TestClient(app)

    try:
        yield client, store
    finally:
        app.dependency_overrides.pop(
            get_satellite_observation_store,
            None,
        )


def _create_observation(
    store,
    *,
    source_image_id="S1D_API_TEST_SCENE",
):
    return store.create_satellite_observation(
        observation_type="sar_scene",
        sensor="Sentinel-1",
        platform="D",
        dataset_id="COPERNICUS/S1_GRD",
        source_image_id=source_image_id,
        acquisition_time="2026-09-17T03:31:58Z",
        processing_time="2026-09-17T18:32:38Z",
        bbox_min_lon=37.55,
        bbox_min_lat=44.55,
        bbox_max_lon=38.15,
        bbox_max_lat=44.95,
        provenance={
            "data_provider": "Copernicus Sentinel-1",
            "processing_platform": "Google Earth Engine",
        },
    )


def test_get_satellite_observations_returns_200_and_list(
    satellite_api,
):
    client, _store = satellite_api

    response = client.get(
        "/satellite/observations/"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_satellite_observations_contains_created_observation(
    satellite_api,
):
    client, store = satellite_api

    observation_id = _create_observation(
        store
    )

    response = client.get(
        "/satellite/observations/"
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["id"] == observation_id
    assert payload[0]["information_type"] == (
        "satellite_observation"
    )
    assert payload[0]["dataset_id"] == (
        "COPERNICUS/S1_GRD"
    )


def test_get_satellite_observation_by_id_returns_200(
    satellite_api,
):
    client, store = satellite_api

    observation_id = _create_observation(
        store
    )

    response = client.get(
        f"/satellite/observations/{observation_id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == observation_id
    assert payload["observation_type"] == "sar_scene"
    assert payload["sensor"] == "Sentinel-1"
    assert payload["provenance"] == {
        "data_provider": "Copernicus Sentinel-1",
        "processing_platform": "Google Earth Engine",
    }


def test_get_satellite_observation_missing_returns_404(
    satellite_api,
):
    client, _store = satellite_api

    response = client.get(
        "/satellite/observations/satobs_missing"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Satellite observation not found"
    }


def test_read_only_satellite_api_does_not_mutate_store(
    satellite_api,
):
    client, store = satellite_api

    observation_id = _create_observation(
        store
    )

    before = store.get_satellite_observation(
        observation_id
    )

    list_response = client.get(
        "/satellite/observations/"
    )
    detail_response = client.get(
        f"/satellite/observations/{observation_id}"
    )

    after = store.get_satellite_observation(
        observation_id
    )

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert after == before
