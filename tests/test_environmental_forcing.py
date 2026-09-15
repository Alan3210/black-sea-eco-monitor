from datetime import datetime, timezone

import pytest

from agents.ocean_data.environmental_forcing import (
    EnvironmentalForcingInputError,
    direction_from_deg,
    direction_to_deg,
    nearest_three_hour_step,
    normalize_target_time,
    validate_location,
    vector_speed,
)


def test_normalize_target_time_floors_to_hour():
    value = normalize_target_time(
        "2026-09-15T10:42:19+00:00"
    )

    assert value == datetime(
        2026,
        9,
        15,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_validate_location_accepts_black_sea_point():
    validate_location(
        37.7691,
        44.7240,
    )


def test_validate_location_rejects_outside_domain():
    with pytest.raises(
        EnvironmentalForcingInputError
    ):
        validate_location(
            10,
            44,
        )


def test_vector_speed():
    assert vector_speed(
        3,
        4,
    ) == 5


def test_direction_to_uses_clockwise_from_north():
    assert direction_to_deg(
        1,
        0,
    ) == pytest.approx(
        90
    )

    assert direction_to_deg(
        0,
        1,
    ) == pytest.approx(
        0
    )


def test_wind_direction_from_is_opposite_direction_to():
    assert direction_from_deg(
        1,
        0,
    ) == pytest.approx(
        270
    )


def test_zero_vector_has_no_direction():
    assert direction_to_deg(
        0,
        0,
    ) is None

    assert direction_from_deg(
        0,
        0,
    ) is None


def test_nearest_three_hour_step():
    run = datetime(
        2026,
        9,
        15,
        0,
        tzinfo=timezone.utc,
    )

    target = datetime(
        2026,
        9,
        15,
        10,
        tzinfo=timezone.utc,
    )

    assert nearest_three_hour_step(
        target,
        run,
    ) == 9


def test_nearest_three_hour_step_rejects_target_before_run():
    run = datetime(
        2026,
        9,
        15,
        12,
        tzinfo=timezone.utc,
    )

    target = datetime(
        2026,
        9,
        15,
        10,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        EnvironmentalForcingInputError
    ):
        nearest_three_hour_step(
            target,
            run,
        )


def test_copernicus_sampler_skips_nearest_land_nan_cell():
    import numpy as np
    import xarray as xr

    from agents.ocean_data.environmental_forcing import (
        _point_from_dataset,
    )

    dataset = xr.Dataset(
        data_vars={
            "uo": (
                ("time", "depth", "latitude", "longitude"),
                np.array(
                    [[[
                        [np.nan, 0.20, 0.30],
                        [0.10, 0.25, 0.35],
                        [0.05, 0.15, 0.40],
                    ]]]
                ),
            ),
            "vo": (
                ("time", "depth", "latitude", "longitude"),
                np.array(
                    [[[
                        [np.nan, 0.02, 0.03],
                        [0.01, 0.025, 0.035],
                        [0.005, 0.015, 0.04],
                    ]]]
                ),
            ),
        },
        coords={
            "time": [
                np.datetime64(
                    "2026-09-15T10:00:00"
                )
            ],
            "depth": [0.5],
            "latitude": [
                44.70,
                44.725,
                44.75,
            ],
            "longitude": [
                37.75,
                37.775,
                37.80,
            ],
        },
    )

    values, valid_time, sampled = (
        _point_from_dataset(
            dataset,
            longitude=37.751,
            latitude=44.701,
            variable_names=(
                "uo",
                "vo",
            ),
        )
    )

    assert values["uo"] == pytest.approx(
        0.20
    )
    assert values["vo"] == pytest.approx(
        0.02
    )
    assert sampled["method"] == (
        "nearest_finite_ocean_cell"
    )
    assert sampled["distance_km"] > 0
    assert valid_time is not None


def test_copernicus_sampler_rejects_all_nan_neighbourhood():
    import numpy as np
    import xarray as xr

    from agents.ocean_data.environmental_forcing import (
        EnvironmentalForcingError,
        _point_from_dataset,
    )

    dataset = xr.Dataset(
        data_vars={
            "uo": (
                ("latitude", "longitude"),
                np.full(
                    (2, 2),
                    np.nan,
                ),
            ),
            "vo": (
                ("latitude", "longitude"),
                np.full(
                    (2, 2),
                    np.nan,
                ),
            ),
        },
        coords={
            "latitude": [
                44.70,
                44.72,
            ],
            "longitude": [
                37.75,
                37.77,
            ],
        },
    )

    with pytest.raises(
        EnvironmentalForcingError
    ):
        _point_from_dataset(
            dataset,
            longitude=37.76,
            latitude=44.71,
            variable_names=(
                "uo",
                "vo",
            ),
        )



def test_iso_utc_formats_numpy_datetime64_instead_of_nanoseconds():
    import numpy as np

    from agents.ocean_data.environmental_forcing import (
        _iso_utc,
    )

    assert _iso_utc(
        np.datetime64(
            "2026-09-15T12:00:00.000000000"
        )
    ) == "2026-09-15T12:00:00+00:00"


def test_time_alignment_reports_zero_for_same_model_hour():
    from agents.ocean_data.environmental_forcing import (
        _time_offset_minutes,
    )

    target = datetime(
        2026,
        9,
        15,
        12,
        0,
        tzinfo=timezone.utc,
    )

    assert _time_offset_minutes(
        "2026-09-15T12:00:00+00:00",
        target,
    ) == 0.0
