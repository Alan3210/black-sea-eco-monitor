from datetime import datetime, timezone

import numpy as np
import xarray as xr

from agents.ocean_data.copernicus_currents import (
    DATASET_ID,
    build_currents_payload,
    direction_degrees,
    normalize_target_time,
)


def make_dataset():
    return xr.Dataset(
        data_vars={
            "uo": (
                (
                    "time",
                    "depth",
                    "latitude",
                    "longitude",
                ),
                np.array(
                    [[[
                        [1.0, 0.0],
                        [0.0, -1.0],
                    ]]]
                ),
            ),
            "vo": (
                (
                    "time",
                    "depth",
                    "latitude",
                    "longitude",
                ),
                np.array(
                    [[[
                        [0.0, 1.0],
                        [-1.0, 0.0],
                    ]]]
                ),
            ),
        },
        coords={
            "time": [
                np.datetime64(
                    "2026-09-15T06:00:00"
                )
            ],
            "depth": [0.5001727938652039],
            "latitude": [41.0, 42.0],
            "longitude": [30.0, 31.0],
        },
    )


def test_normalizes_requested_time_to_utc_hour():
    result = normalize_target_time(
        "2026-09-15T09:44:12+03:00"
    )

    assert result == datetime(
        2026,
        9,
        15,
        6,
        0,
        tzinfo=timezone.utc,
    )


def test_direction_is_clockwise_from_north():
    assert direction_degrees(0.0, 1.0) == 0.0
    assert direction_degrees(1.0, 0.0) == 90.0
    assert direction_degrees(0.0, -1.0) == 180.0
    assert direction_degrees(-1.0, 0.0) == 270.0


def test_builds_surface_current_vector_payload():
    target = datetime(
        2026,
        9,
        15,
        6,
        tzinfo=timezone.utc,
    )

    payload = build_currents_payload(
        make_dataset(),
        target_time=target,
        stride=1,
    )

    assert payload["dataset_id"] == DATASET_ID
    assert payload["vector_count"] == 4
    assert payload["depth_m"] > 0
    assert payload["variable_units"] == "m/s"

    first = payload["vectors"][0]

    assert first["latitude"] == 41.0
    assert first["longitude"] == 30.0
    assert first["u"] == 1.0
    assert first["v"] == 0.0
    assert first["speed"] == 1.0
    assert first["direction_deg"] == 90.0
