import pytest
from fastapi.testclient import TestClient

from agents.news_agent.event_store import EventStore
from backend.api.satellite_observations import (
    get_satellite_observation_store,
)
from backend.main import app


@pytest.fixture
def satellite_api(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    source_scene_a = "S1D_SCENE_A"
    source_scene_b = "S1D_SCENE_B"

    processed_id = (
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id=source_scene_a,
            acquisition_time="2026-09-17T03:31:58Z",
            derivation_level="processed",
        )
    )

    candidate_a = (
        store.create_satellite_observation(
            observation_type="sar_dark_spot_candidate",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id=source_scene_a,
            acquisition_time="2026-09-17T03:31:58Z",
            derivation_level="derived",
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        [37.65, 44.56],
                        [37.66, 44.56],
                        [37.66, 44.57],
                        [37.65, 44.57],
                        [37.65, 44.56],
                    ]
                ],
            },
            bbox_min_lon=37.65,
            bbox_min_lat=44.56,
            bbox_max_lon=37.66,
            bbox_max_lat=44.57,
            provenance={
                "candidate_id": "sar_ds_001",
                "area_km2": 0.013,
                "mean_vv_db": -25.8,
                "threshold_db": -24.0,
            },
        )
    )

    candidate_b = (
        store.create_satellite_observation(
            observation_type="sar_dark_spot_candidate",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id=source_scene_b,
            acquisition_time="2026-09-16T03:31:58Z",
            derivation_level="derived",
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        [37.70, 44.60],
                        [37.71, 44.60],
                        [37.71, 44.61],
                        [37.70, 44.61],
                        [37.70, 44.60],
                    ]
                ],
            },
            bbox_min_lon=37.70,
            bbox_min_lat=44.60,
            bbox_max_lon=37.71,
            bbox_max_lat=44.61,
            provenance={
                "candidate_id": "sar_ds_002",
                "area_km2": 0.011,
                "mean_vv_db": -25.5,
                "threshold_db": -24.0,
            },
        )
    )

    app.dependency_overrides[
        get_satellite_observation_store
    ] = lambda: store

    client = TestClient(app)

    try:
        yield (
            client,
            store,
            processed_id,
            candidate_a,
            candidate_b,
            source_scene_a,
            source_scene_b,
        )
    finally:
        app.dependency_overrides.pop(
            get_satellite_observation_store,
            None,
        )


def test_collection_filter_by_observation_type(
    satellite_api,
):
    client, *_ = satellite_api

    response = client.get(
        "/satellite/observations/",
        params={
            "observation_type": (
                "sar_dark_spot_candidate"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 2
    assert {
        item["observation_type"]
        for item in payload
    } == {
        "sar_dark_spot_candidate"
    }


def test_collection_filter_by_derivation_level(
    satellite_api,
):
    client, *_ = satellite_api

    response = client.get(
        "/satellite/observations/",
        params={
            "derivation_level": "processed"
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0][
        "observation_type"
    ] == "sar_scene"


def test_collection_filter_by_source_image_id(
    satellite_api,
):
    (
        client,
        _store,
        _processed_id,
        candidate_a,
        _candidate_b,
        source_scene_a,
        _source_scene_b,
    ) = satellite_api

    response = client.get(
        "/satellite/observations/",
        params={
            "observation_type": (
                "sar_dark_spot_candidate"
            ),
            "source_image_id": source_scene_a,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["id"] == candidate_a


def test_collection_combined_filters_can_return_empty(
    satellite_api,
):
    (
        client,
        _store,
        _processed_id,
        _candidate_a,
        _candidate_b,
        _source_scene_a,
        source_scene_b,
    ) = satellite_api

    response = client.get(
        "/satellite/observations/",
        params={
            "observation_type": "sar_scene",
            "derivation_level": "derived",
            "source_image_id": source_scene_b,
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_candidate_geojson_returns_only_derived_candidates(
    satellite_api,
):
    client, *_ = satellite_api

    response = client.get(
        "/satellite/observations/candidates.geojson"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 2
    assert "oil_spill" in payload[
        "semantics"
    ][
        "does_not_mean"
    ]

    feature = payload["features"][0]

    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Polygon"
    assert feature["properties"][
        "observation_type"
    ] == "sar_dark_spot_candidate"
    assert feature["properties"][
        "derivation_level"
    ] == "derived"
    assert feature["properties"][
        "candidate_id"
    ] is not None


def test_candidate_geojson_filter_by_source_scene(
    satellite_api,
):
    (
        client,
        _store,
        _processed_id,
        candidate_a,
        _candidate_b,
        source_scene_a,
        _source_scene_b,
    ) = satellite_api

    response = client.get(
        "/satellite/observations/candidates.geojson",
        params={
            "source_image_id": source_scene_a
        },
    )

    assert response.status_code == 200

    features = response.json()[
        "features"
    ]

    assert len(features) == 1
    assert features[0][
        "properties"
    ][
        "observation_id"
    ] == candidate_a


def test_existing_detail_route_still_works(
    satellite_api,
):
    (
        client,
        _store,
        processed_id,
        *_rest,
    ) = satellite_api

    response = client.get(
        f"/satellite/observations/{processed_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == processed_id
