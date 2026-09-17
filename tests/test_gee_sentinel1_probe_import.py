from copy import deepcopy

import pytest

from agents.news_agent.event_store import EventStore
from backend.services.satellite.gee_probe_import import (
    GeeProbeImportError,
    build_observation_kwargs,
    derive_bbox_from_geometry,
    import_probe_scene,
)


@pytest.fixture
def sample_probe():
    return {
        "probe_version": "0.1",
        "information_type": "satellite_observation",
        "derivation_level": "processed",
        "generated_at": (
            "2026-09-17T18:32:38.792208+00:00"
        ),
        "aoi": {
            "name": "Novorossiysk",
            "bbox": [
                37.55,
                44.55,
                38.15,
                44.95,
            ],
        },
        "query": {
            "dataset_id": "COPERNICUS/S1_GRD",
            "instrument_mode": "IW",
            "resolution_meters": 10,
            "required_polarization": "VV",
        },
        "provenance": {
            "data_provider": (
                "Copernicus Sentinel-1"
            ),
            "processing_platform": (
                "Google Earth Engine"
            ),
            "source_level": "GRD",
            "gee_representation": (
                "sigma0_backscatter_db"
            ),
        },
        "scenes": [
            {
                "acquisition_time": (
                    "2026-09-17T03:31:58Z"
                ),
                "instrument_mode": "IW",
                "orbit_pass": "DESCENDING",
                "platform_number": "D",
                "polarizations": [
                    "VV",
                    "VH",
                ],
                "relative_orbit": 21,
                "resolution_meters": 10,
                "scene_id": "S1D_TEST_SCENE",
                "system_index": "S1D_TEST_SCENE",
                "footprint_bounds": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                37.035559,
                                42.866474,
                            ],
                            [
                                40.471964,
                                42.866474,
                            ],
                            [
                                40.471964,
                                44.756783,
                            ],
                            [
                                37.035559,
                                44.756783,
                            ],
                            [
                                37.035559,
                                42.866474,
                            ],
                        ]
                    ],
                },
            }
        ],
    }


def test_mapping_preserves_satellite_semantics(
    sample_probe,
):
    kwargs = build_observation_kwargs(
        sample_probe
    )

    assert kwargs["observation_type"] == "sar_scene"
    assert kwargs["sensor"] == "Sentinel-1"
    assert kwargs["platform"] == "D"
    assert kwargs["dataset_id"] == "COPERNICUS/S1_GRD"
    assert kwargs["source_image_id"] == "S1D_TEST_SCENE"
    assert kwargs["derivation_level"] == "processed"
    assert kwargs["confidence"] is None
    assert kwargs["review_status"] == "unreviewed"
    assert kwargs["processing_version"] == "0.1"
    assert kwargs["processing_method"] == (
        "gee_sentinel1_probe"
    )


def test_bbox_comes_from_scene_footprint_not_query_aoi(
    sample_probe,
):
    kwargs = build_observation_kwargs(
        sample_probe
    )

    assert (
        kwargs["bbox_min_lon"],
        kwargs["bbox_min_lat"],
        kwargs["bbox_max_lon"],
        kwargs["bbox_max_lat"],
    ) == pytest.approx(
        (
            37.035559,
            42.866474,
            40.471964,
            44.756783,
        )
    )

    assert (
        kwargs["bbox_min_lon"]
        != sample_probe["aoi"]["bbox"][0]
    )


def test_provenance_keeps_probe_and_scene_metadata(
    sample_probe,
):
    kwargs = build_observation_kwargs(
        sample_probe
    )

    provenance = kwargs["provenance"]

    assert provenance["processing_platform"] == (
        "Google Earth Engine"
    )
    assert provenance["probe_version"] == "0.1"
    assert provenance["probe_aoi"]["name"] == (
        "Novorossiysk"
    )
    assert provenance["scene_metadata"][
        "orbit_pass"
    ] == "DESCENDING"
    assert provenance["scene_metadata"][
        "relative_orbit"
    ] == 21


def test_import_creates_real_store_record(
    tmp_path,
    sample_probe,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    result = import_probe_scene(
        store,
        sample_probe,
    )

    assert result["created"] is True

    record = store.get_satellite_observation(
        result["observation_id"]
    )

    assert record["source_image_id"] == (
        "S1D_TEST_SCENE"
    )
    assert record["information_type"] == (
        "satellite_observation"
    )
    assert record["confidence"] is None
    assert record["geometry"]["type"] == "Polygon"


def test_import_is_idempotent_for_same_scene_and_version(
    tmp_path,
    sample_probe,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    first = import_probe_scene(
        store,
        sample_probe,
    )
    second = import_probe_scene(
        store,
        sample_probe,
    )

    assert first["created"] is True
    assert second["created"] is False
    assert (
        second["observation_id"]
        == first["observation_id"]
    )
    assert len(
        store.list_satellite_observations()
    ) == 1


def test_rejects_non_satellite_probe(
    sample_probe,
):
    broken = deepcopy(
        sample_probe
    )
    broken["information_type"] = (
        "model_forecast"
    )

    with pytest.raises(
        GeeProbeImportError,
        match="information_type",
    ):
        build_observation_kwargs(
            broken
        )


def test_rejects_probe_without_saved_scenes(
    sample_probe,
):
    broken = deepcopy(
        sample_probe
    )
    broken["scenes"] = []

    with pytest.raises(
        GeeProbeImportError,
        match="no saved scenes",
    ):
        build_observation_kwargs(
            broken
        )


def test_rejects_footprint_without_coordinates():
    with pytest.raises(
        GeeProbeImportError,
        match="no coordinates",
    ):
        derive_bbox_from_geometry(
            {
                "type": "Polygon",
                "coordinates": [],
            }
        )
