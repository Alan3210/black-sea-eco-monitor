from copy import deepcopy

import pytest

from tools.gee_sentinel1_dark_spot_candidates_v01 import (
    CandidateExtractionError,
    bbox_from_geojson_geometry,
    build_output_skeleton,
    min_connected_pixels,
    normalize_candidate_features,
    select_probe_scene,
    validate_calibration_scene,
    validate_threshold,
)


@pytest.fixture
def probe():
    return {
        "information_type": "satellite_observation",
        "aoi": {
            "name": "Novorossiysk",
            "bbox": [
                37.55,
                44.55,
                38.15,
                44.95,
            ],
        },
        "provenance": {
            "data_provider": "Copernicus Sentinel-1",
            "processing_platform": "Google Earth Engine",
            "dataset_id": "COPERNICUS/S1_GRD",
            "source_level": "GRD",
            "gee_representation": "sigma0_backscatter_db",
        },
        "scenes": [
            {
                "scene_id": "S1D_TEST_SCENE",
                "system_index": "S1D_TEST_SCENE",
                "acquisition_time": "2026-09-17T03:31:58Z",
                "platform_number": "D",
                "orbit_pass": "DESCENDING",
                "relative_orbit": 21,
                "instrument_mode": "IW",
                "polarizations": ["VV", "VH"],
            }
        ],
    }


@pytest.fixture
def calibration():
    return {
        "calibration_version": "0.1",
        "analysis_type": "sar_vv_calibration",
        "scene": {
            "scene_id": "S1D_TEST_SCENE",
        },
        "vv_db": {
            "percentiles": {
                "p01": -25.12,
                "p05": -22.87,
                "p10": -21.87,
                "p25": -20.12,
                "p50": -18.38,
            }
        },
        "threshold_tests": {
            "-24": {
                "candidate_area_km2": 9.902,
            }
        },
    }


def test_min_connected_pixels_for_one_hectare():
    assert min_connected_pixels(
        min_area_km2=0.01
    ) == 100


def test_threshold_accepts_minus_24():
    assert validate_threshold(
        -24.0
    ) == -24.0


@pytest.mark.parametrize(
    "threshold",
    [-30.0, -31.0, 0.0, 1.0],
)
def test_threshold_rejects_invalid_range(
    threshold,
):
    with pytest.raises(
        CandidateExtractionError
    ):
        validate_threshold(
            threshold
        )


def test_calibration_must_match_scene(
    probe,
    calibration,
):
    scene = select_probe_scene(
        probe,
        scene_index=0,
    )

    broken = deepcopy(
        calibration
    )
    broken["scene"]["scene_id"] = (
        "OTHER_SCENE"
    )

    with pytest.raises(
        CandidateExtractionError,
        match="does not match",
    ):
        validate_calibration_scene(
            broken,
            scene,
        )


def test_output_semantics_are_non_confirmatory(
    probe,
    calibration,
):
    scene = select_probe_scene(
        probe,
        scene_index=0,
    )

    output = build_output_skeleton(
        probe,
        calibration,
        scene,
        threshold_db=-24.0,
        min_area_km2=0.01,
        min_pixels=100,
    )

    assert output["information_type"] == (
        "satellite_observation"
    )
    assert output["derivation_level"] == (
        "derived"
    )
    assert output["observation_type"] == (
        "sar_dark_spot_candidate"
    )
    assert output["analysis"]["threshold_db"] == (
        -24.0
    )
    assert "oil_spill" in output[
        "semantics"
    ]["does_not_mean"]
    assert output["candidates"] == []


def test_bbox_from_geojson_polygon():
    geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [37.1, 44.1],
                [37.5, 44.1],
                [37.5, 44.4],
                [37.1, 44.4],
                [37.1, 44.1],
            ]
        ],
    }

    assert bbox_from_geojson_geometry(
        geometry
    ) == [
        37.1,
        44.1,
        37.5,
        44.4,
    ]


def test_candidate_normalization():
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [37.1, 44.1],
                            [37.2, 44.1],
                            [37.2, 44.2],
                            [37.1, 44.2],
                            [37.1, 44.1],
                        ]
                    ],
                },
                "properties": {
                    "area_m2": 12500.0,
                    "mean_vv_db": -25.4,
                },
            }
        ],
    }

    candidates = (
        normalize_candidate_features(
            fc
        )
    )

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == (
        "sar_ds_001"
    )
    assert candidates[0]["area_km2"] == (
        0.0125
    )
    assert candidates[0]["mean_vv_db"] == (
        -25.4
    )
    assert candidates[0]["review_status"] == (
        "unreviewed"
    )
    assert candidates[0]["confidence"] is None
