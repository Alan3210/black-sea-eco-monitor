from copy import deepcopy

import pytest

from tools.build_sat7c_verification_map_v01 import (
    VerificationError,
    bbox_center,
    build_summary,
    candidate_summaries,
    haversine_km,
    pairwise_candidate_distances,
    validate_candidate_payload,
)


@pytest.fixture
def payload():
    return {
        "information_type": "satellite_observation",
        "derivation_level": "derived",
        "observation_type": "sar_dark_spot_candidate",
        "source_scene": {
            "scene_id": "S1D_TEST_SCENE",
        },
        "analysis": {
            "threshold_db": -24.0,
        },
        "summary": {
            "candidate_count": 2,
        },
        "candidates": [
            {
                "candidate_id": "sar_ds_001",
                "review_status": "unreviewed",
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
                    "type": "Polygon",
                    "coordinates": [],
                },
            },
            {
                "candidate_id": "sar_ds_002",
                "review_status": "unreviewed",
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
                    "type": "Polygon",
                    "coordinates": [],
                },
            },
        ],
        "semantics": {
            "result_type": "sar_dark_spot_candidate",
        },
    }


@pytest.fixture
def events():
    return [
        {
            "id": "evt_test",
            "category": "industrial_fire",
            "location_name": "Novorossiysk",
            "status": "detected",
            "latitude": 44.724,
            "longitude": 37.7691,
        }
    ]


def test_validate_candidate_payload_accepts_sat7b(
    payload,
):
    validate_candidate_payload(
        payload
    )


def test_validate_candidate_payload_rejects_wrong_type(
    payload,
):
    broken = deepcopy(
        payload
    )
    broken["observation_type"] = "oil_spill"

    with pytest.raises(
        VerificationError
    ):
        validate_candidate_payload(
            broken
        )


def test_bbox_center():
    lat, lon = bbox_center(
        [
            37.0,
            44.0,
            38.0,
            45.0,
        ]
    )

    assert lat == 44.5
    assert lon == 37.5


def test_haversine_zero_distance():
    assert haversine_km(
        44.0,
        37.0,
        44.0,
        37.0,
    ) == pytest.approx(
        0.0
    )


def test_candidate_summaries_include_nearest_event(
    payload,
    events,
):
    summaries = candidate_summaries(
        payload,
        events,
    )

    assert len(summaries) == 2
    assert summaries[0][
        "nearest_event"
    ]["event_id"] == "evt_test"
    assert summaries[0][
        "nearest_event"
    ]["distance_km"] > 0.0


def test_pairwise_distances(
    payload,
    events,
):
    summaries = candidate_summaries(
        payload,
        events,
    )

    distances = pairwise_candidate_distances(
        summaries
    )

    assert len(distances) == 1
    assert distances[0][
        "candidate_a"
    ] == "sar_ds_001"
    assert distances[0][
        "candidate_b"
    ] == "sar_ds_002"
    assert distances[0][
        "distance_km"
    ] > 0.0


def test_build_summary_preserves_non_confirmatory_semantics(
    payload,
    events,
):
    summary = build_summary(
        payload,
        events,
    )

    assert summary[
        "verification_type"
    ] == "visual_spatial_review"
    assert summary[
        "candidate_count"
    ] == 2
    assert "oil_spill" in summary[
        "semantics"
    ]["does_not_mean"]
    assert "confirmed_pollution" in summary[
        "semantics"
    ]["does_not_mean"]
