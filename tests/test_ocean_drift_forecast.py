from datetime import datetime, timezone

import numpy as np
import pytest
import xarray as xr

from agents.ocean_data.drift_forecast import (
    OceanDriftInputError,
    build_drift_payload,
    forcing_bbox,
    requested_horizons,
    summarize_points,
    validate_drift_request,
)


def test_requested_horizons_are_cumulative():
    assert requested_horizons(6) == (6,)
    assert requested_horizons(24) == (6, 12, 24)
    assert requested_horizons(72) == (
        6,
        12,
        24,
        48,
        72,
    )


def test_rejects_unsupported_horizon():
    with pytest.raises(
        OceanDriftInputError
    ):
        requested_horizons(18)


def test_validates_request_limits():
    validate_drift_request(
        longitude=37.7691,
        latitude=44.7240,
        hours=24,
        particles=500,
        radius_m=500,
        diffusivity_m2_s=2,
    )

    with pytest.raises(
        OceanDriftInputError
    ):
        validate_drift_request(
            longitude=0,
            latitude=44,
            hours=24,
            particles=500,
            radius_m=500,
            diffusivity_m2_s=2,
        )


def test_forcing_bbox_is_clipped_to_black_sea_domain():
    bbox = forcing_bbox(
        longitude=41.5,
        latitude=47.0,
    )

    assert bbox["east"] <= 42.0
    assert bbox["north"] <= 47.32500076293945


def test_summarize_points_returns_center_bbox_and_polygon():
    summary = summarize_points([
        [30.0, 43.0],
        [31.0, 43.0],
        [31.0, 44.0],
        [30.0, 44.0],
    ])

    assert summary["particle_count"] == 4
    assert summary["center"] == {
        "longitude": 30.5,
        "latitude": 43.5,
    }
    assert summary["bbox"] == {
        "west": 30.0,
        "south": 43.0,
        "east": 31.0,
        "north": 44.0,
    }
    assert (
        summary["envelope"]["type"]
        == "Polygon"
    )


def test_build_drift_payload_extracts_horizons_and_mean_track():
    start = datetime(
        2026,
        9,
        15,
        8,
        tzinfo=timezone.utc,
    )

    times = np.array(
        [
            np.datetime64(
                "2026-09-15T08:00:00"
            )
            + np.timedelta64(
                hour,
                "h",
            )
            for hour in range(25)
        ]
    )

    trajectories = 3

    lon = np.zeros(
        (
            trajectories,
            len(times),
        ),
        dtype=float,
    )
    lat = np.zeros_like(lon)
    status = np.zeros_like(lon)

    for particle in range(
        trajectories
    ):
        for hour in range(
            len(times)
        ):
            lon[particle, hour] = (
                37.0
                + particle * 0.01
                + hour * 0.001
            )
            lat[particle, hour] = (
                44.0
                + particle * 0.01
                + hour * 0.0005
            )

    result = xr.Dataset(
        data_vars={
            "lon": (
                ("trajectory", "time"),
                lon,
            ),
            "lat": (
                ("trajectory", "time"),
                lat,
            ),
            "status": (
                ("trajectory", "time"),
                status,
            ),
        },
        coords={
            "trajectory": np.arange(
                trajectories
            ),
            "time": times,
        },
    )

    payload = build_drift_payload(
        result,
        start_time=start,
        longitude=37.0,
        latitude=44.0,
        hours=24,
        particles=3,
        radius_m=100,
        diffusivity_m2_s=2,
        opendrift_version="1.14.11",
    )

    assert payload["model"] == (
        "OpenDrift OceanDrift"
    )
    assert payload["model_version"] == (
        "1.14.11"
    )
    assert [
        item["hours"]
        for item in payload["horizons"]
    ] == [
        6,
        12,
        24,
    ]
    assert len(
        payload["mean_track"]
    ) == 25
    assert (
        payload["horizons"][-1][
            "particle_count"
        ]
        == 3
    )
