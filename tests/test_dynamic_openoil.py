from datetime import datetime, timezone

import numpy as np
import pytest
import xarray as xr

from agents.ocean_data.dynamic_openoil import (
    DynamicOpenOilInputError,
    _requested_horizons,
    nearest_finite_ocean_cell,
    snapshot_at_horizon,
    validate_dynamic_openoil_request,
)


def test_validate_dynamic_openoil_request():
    validate_dynamic_openoil_request(
        hours=6,
        particles=100,
        radius_m=200,
        release_volume_m3=1,
        half_width_deg=1.0,
    )


def test_validate_dynamic_openoil_rejects_bad_horizon():
    with pytest.raises(
        DynamicOpenOilInputError
    ):
        validate_dynamic_openoil_request(
            hours=18,
            particles=100,
            radius_m=200,
            release_volume_m3=1,
            half_width_deg=1.0,
        )


def test_requested_horizons_are_cumulative():
    assert _requested_horizons(
        72
    ) == (
        6,
        12,
        24,
        48,
        72,
    )


def test_nearest_finite_ocean_cell_skips_masked_land():
    dataset = xr.Dataset(
        data_vars={
            "uo": (
                (
                    "time",
                    "depth",
                    "latitude",
                    "longitude",
                ),
                np.array([
                    [[
                        [np.nan, 0.1],
                        [0.2, 0.3],
                    ]]
                ]),
            ),
            "vo": (
                (
                    "time",
                    "depth",
                    "latitude",
                    "longitude",
                ),
                np.array([
                    [[
                        [np.nan, 0.1],
                        [0.2, 0.3],
                    ]]
                ]),
            ),
        },
        coords={
            "time": [
                np.datetime64(
                    "2026-09-15T13:00:00"
                )
            ],
            "depth": [0.5],
            "latitude": [
                44.70,
                44.725,
            ],
            "longitude": [
                37.80,
                37.825,
            ],
        },
    )

    seed = nearest_finite_ocean_cell(
        dataset,
        longitude=37.80,
        latitude=44.70,
    )

    assert seed[
        "method"
    ] == (
        "nearest_finite_dynamic_ocean_cell"
    )
    assert not (
        seed["longitude"] == 37.80
        and seed["latitude"] == 44.70
    )


def test_snapshot_at_horizon_uses_last_finite_observation_before_target():
    start = datetime(
        2026,
        9,
        15,
        13,
        tzinfo=timezone.utc,
    )

    times = np.array([
        np.datetime64(
            "2026-09-15T13:00:00"
        ),
        np.datetime64(
            "2026-09-15T14:00:00"
        ),
        np.datetime64(
            "2026-09-15T15:00:00"
        ),
    ])

    result = xr.Dataset(
        data_vars={
            "lon": (
                ("trajectory", "time"),
                np.array([
                    [37.0, 37.1, np.nan],
                    [38.0, 38.1, 38.2],
                ]),
            ),
            "lat": (
                ("trajectory", "time"),
                np.array([
                    [44.0, 44.1, np.nan],
                    [45.0, 45.1, 45.2],
                ]),
            ),
        },
        coords={
            "trajectory": [0, 1],
            "time": times,
        },
    )

    snapshot = snapshot_at_horizon(
        result,
        start_time=start,
        hours=2,
    )

    assert snapshot[
        "trajectory_count"
    ] == 2
    assert snapshot[
        "particle_count"
    ] == 2
    assert snapshot[
        "center"
    ] == {
        "longitude": 37.65,
        "latitude": 44.65,
    }


def test_snapshot_at_horizon_has_requested_hour():
    start = datetime(
        2026,
        9,
        15,
        13,
        tzinfo=timezone.utc,
    )

    times = np.array([
        np.datetime64(
            "2026-09-15T13:00:00"
        ),
        np.datetime64(
            "2026-09-15T19:00:00"
        ),
    ])

    result = xr.Dataset(
        data_vars={
            "lon": (
                ("trajectory", "time"),
                np.array([
                    [37.0, 37.2]
                ]),
            ),
            "lat": (
                ("trajectory", "time"),
                np.array([
                    [44.0, 44.2]
                ]),
            ),
        },
        coords={
            "trajectory": [0],
            "time": times,
        },
    )

    snapshot = snapshot_at_horizon(
        result,
        start_time=start,
        hours=6,
    )

    assert snapshot[
        "hours"
    ] == 6
    assert snapshot[
        "time"
    ] == (
        "2026-09-15T19:00:00+00:00"
    )



def test_result_time_bounds_and_completion_detection():
    from agents.ocean_data.dynamic_openoil import (
        result_time_bounds,
        simulation_reached_requested_end,
    )

    result = xr.Dataset(
        coords={
            "time": np.array([
                np.datetime64("2026-09-15T13:00:00"),
                np.datetime64("2026-09-15T19:00:00"),
            ]),
        },
    )

    bounds = result_time_bounds(result)
    assert bounds["start_time"] == "2026-09-15T13:00:00+00:00"
    assert bounds["end_time"] == "2026-09-15T19:00:00+00:00"
    assert simulation_reached_requested_end(
        result,
        datetime(2026, 9, 15, 19, tzinfo=timezone.utc),
    ) is True


def test_completion_detection_rejects_early_stop():
    from agents.ocean_data.dynamic_openoil import (
        simulation_reached_requested_end,
    )

    result = xr.Dataset(
        coords={
            "time": np.array([
                np.datetime64("2026-09-15T13:00:00"),
                np.datetime64("2026-09-15T17:00:00"),
            ]),
        },
    )

    assert simulation_reached_requested_end(
        result,
        datetime(2026, 9, 15, 19, tzinfo=timezone.utc),
    ) is False



def test_completion_classifies_requested_end_as_complete():
    from agents.ocean_data.dynamic_openoil import (
        classify_dynamic_run_completion,
    )

    result = classify_dynamic_run_completion(
        reached_requested_end=True,
        runtime_state={
            "physical_terminal_state": False,
        },
    )

    assert result[
        "forecast_complete"
    ] is True
    assert result[
        "completion_reason"
    ] == "requested_end_reached"


def test_completion_classifies_all_stranded_as_terminal_complete():
    from agents.ocean_data.dynamic_openoil import (
        classify_dynamic_run_completion,
    )

    result = classify_dynamic_run_completion(
        reached_requested_end=False,
        runtime_state={
            "physical_terminal_state": True,
        },
    )

    assert result[
        "forecast_complete"
    ] is True
    assert result[
        "forecast_status"
    ] == (
        "DYNAMIC_SCIENTIFIC_VALIDATION_TERMINAL"
    )


def test_completion_keeps_unresolved_early_stop_incomplete():
    from agents.ocean_data.dynamic_openoil import (
        classify_dynamic_run_completion,
    )

    result = classify_dynamic_run_completion(
        reached_requested_end=False,
        runtime_state={
            "physical_terminal_state": False,
        },
    )

    assert result[
        "forecast_complete"
    ] is False
    assert result[
        "completion_reason"
    ] == "stopped_early_unresolved"
