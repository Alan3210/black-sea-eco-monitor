from copy import deepcopy

import pytest

from agents.news_agent.event_store import EventStore
from backend.services.satellite.dark_spot_import import (
    DarkSpotImportError,
    build_observation_kwargs,
    import_candidate_payload,
    validate_candidate_payload,
)


@pytest.fixture
def payload():
    return {
        "extraction_version": "0.1",
        "information_type": "satellite_observation",
        "derivation_level": "derived",
        "observation_type": "sar_dark_spot_candidate",
        "generated_at": (
            "2026-09-18T07:43:47+00:00"
        ),
        "source_scene": {
            "scene_id": "S1D_TEST_SCENE",
            "system_index": "S1D_TEST_SCENE",
            "acquisition_time": (
                "2026-09-17T03:31:58Z"
            ),
            "platform_number": "D",
            "orbit_pass": "DESCENDING",
            "relative_orbit": 21,
            "instrument_mode": "IW",
            "polarizations": [
                "VV",
                "VH",
            ],
        },
        "analysis": {
            "threshold_db": -24.0,
            "edge_noise_floor_db": -30.0,
            "min_area_km2": 0.01,
            "min_connected_pixels": 100,
            "connectivity": 8,
            "scale_meters": 10,
            "water_mask": {
                "dataset_id": (
                    "ESA/WorldCover/v200"
                ),
                "band": "Map",
                "class_value": 80,
            },
        },
        "provenance": {
            "data_provider": (
                "Copernicus Sentinel-1"
            ),
            "processing_platform": (
                "Google Earth Engine"
            ),
            "dataset_id": (
                "COPERNICUS/S1_GRD"
            ),
            "source_level": "GRD",
            "gee_representation": (
                "sigma0_backscatter_db"
            ),
            "processing_method": (
                "water_mask + edge_guard + "
                "vv_threshold + connected_components"
            ),
        },
        "semantics": {
            "result_type": (
                "sar_dark_spot_candidate"
            ),
            "does_not_mean": [
                "oil_spill",
                "confirmed_pollution",
                "confirmed_event",
                "causal_link_to_event",
            ],
        },
        "candidates": [
            {
                "candidate_id": (
                    "sar_ds_001"
                ),
                "review_status": (
                    "unreviewed"
                ),
                "confidence": None,
                "area_km2": 0.013,
                "mean_vv_db": -25.8,
                "bbox": [
                    37.65,
                    44.56,
                    37.66,
                    44.57,
                ],
                "geometry": {
                    "type": (
                        "MultiPolygon"
                    ),
                    "coordinates": [
                        [
                            [
                                [
                                    37.65,
                                    44.56,
                                ],
                                [
                                    37.66,
                                    44.56,
                                ],
                                [
                                    37.66,
                                    44.57,
                                ],
                                [
                                    37.65,
                                    44.57,
                                ],
                                [
                                    37.65,
                                    44.56,
                                ],
                            ]
                        ]
                    ],
                },
            },
            {
                "candidate_id": (
                    "sar_ds_002"
                ),
                "review_status": (
                    "unreviewed"
                ),
                "confidence": None,
                "area_km2": 0.011,
                "mean_vv_db": -25.5,
                "bbox": [
                    37.67,
                    44.58,
                    37.68,
                    44.59,
                ],
                "geometry": {
                    "type": (
                        "MultiPolygon"
                    ),
                    "coordinates": [
                        [
                            [
                                [
                                    37.67,
                                    44.58,
                                ],
                                [
                                    37.68,
                                    44.58,
                                ],
                                [
                                    37.68,
                                    44.59,
                                ],
                                [
                                    37.67,
                                    44.59,
                                ],
                                [
                                    37.67,
                                    44.58,
                                ],
                            ]
                        ]
                    ],
                },
            },
        ],
    }


def test_validate_candidate_payload(
    payload,
):
    validate_candidate_payload(
        payload
    )


def test_rejects_wrong_observation_type(
    payload,
):
    broken = deepcopy(
        payload
    )
    broken[
        "observation_type"
    ] = "oil_spill"

    with pytest.raises(
        DarkSpotImportError
    ):
        validate_candidate_payload(
            broken
        )


def test_mapping_preserves_derived_semantics(
    payload,
):
    kwargs = build_observation_kwargs(
        payload,
        payload[
            "candidates"
        ][0],
    )

    assert kwargs[
        "observation_type"
    ] == "sar_dark_spot_candidate"
    assert kwargs[
        "derivation_level"
    ] == "derived"
    assert kwargs[
        "sensor"
    ] == "Sentinel-1"
    assert kwargs[
        "dataset_id"
    ] == "COPERNICUS/S1_GRD"
    assert kwargs[
        "source_image_id"
    ] == "S1D_TEST_SCENE"
    assert kwargs[
        "confidence"
    ] is None
    assert kwargs[
        "review_status"
    ] == "unreviewed"
    assert kwargs[
        "processing_version"
    ] == "0.1"


def test_mapping_preserves_candidate_provenance(
    payload,
):
    kwargs = build_observation_kwargs(
        payload,
        payload[
            "candidates"
        ][0],
    )

    provenance = kwargs[
        "provenance"
    ]

    assert provenance[
        "candidate_id"
    ] == "sar_ds_001"
    assert provenance[
        "area_km2"
    ] == pytest.approx(
        0.013
    )
    assert provenance[
        "mean_vv_db"
    ] == pytest.approx(
        -25.8
    )
    assert provenance[
        "threshold_db"
    ] == -24.0
    assert provenance[
        "min_area_km2"
    ] == 0.01
    assert "oil_spill" in provenance[
        "semantic_disclaimer"
    ][
        "does_not_mean"
    ]


def test_import_creates_one_observation_per_candidate(
    tmp_path,
    payload,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    results = import_candidate_payload(
        store,
        payload,
    )

    assert len(
        results
    ) == 2
    assert all(
        item[
            "created"
        ]
        for item in results
    )

    records = [
        item
        for item in (
            store.list_satellite_observations()
        )
        if item[
            "observation_type"
        ] == (
            "sar_dark_spot_candidate"
        )
    ]

    assert len(
        records
    ) == 2


def test_imported_geometry_and_bbox_round_trip(
    tmp_path,
    payload,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    results = import_candidate_payload(
        store,
        payload,
    )

    first = store.get_satellite_observation(
        results[0][
            "observation_id"
        ]
    )

    assert first[
        "geometry"
    ][
        "type"
    ] == "MultiPolygon"

    assert first[
        "bbox"
    ] == {
        "min_lon": 37.65,
        "min_lat": 44.56,
        "max_lon": 37.66,
        "max_lat": 44.57,
    }


def test_import_is_idempotent_per_candidate(
    tmp_path,
    payload,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    first = import_candidate_payload(
        store,
        payload,
    )
    second = import_candidate_payload(
        store,
        payload,
    )

    assert all(
        item[
            "created"
        ]
        for item in first
    )

    assert all(
        not item[
            "created"
        ]
        for item in second
    )

    assert [
        item[
            "observation_id"
        ]
        for item in first
    ] == [
        item[
            "observation_id"
        ]
        for item in second
    ]

    records = [
        item
        for item in (
            store.list_satellite_observations()
        )
        if item[
            "observation_type"
        ] == (
            "sar_dark_spot_candidate"
        )
    ]

    assert len(
        records
    ) == 2


def test_import_does_not_create_events(
    tmp_path,
    payload,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    before = store.list_event_records()

    import_candidate_payload(
        store,
        payload,
    )

    after = store.list_event_records()

    assert after == before == []


def test_invalid_candidate_bbox_is_rejected(
    payload,
):
    broken = deepcopy(
        payload
    )

    broken[
        "candidates"
    ][0][
        "bbox"
    ] = [
        37.66,
        44.57,
        37.65,
        44.56,
    ]

    with pytest.raises(
        DarkSpotImportError,
        match="bbox",
    ):
        build_observation_kwargs(
            broken,
            broken[
                "candidates"
            ][0],
        )
