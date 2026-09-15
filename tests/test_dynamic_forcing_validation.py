from datetime import datetime, timezone

import numpy as np
import pytest
import xarray as xr

from agents.ocean_data.dynamic_forcing_validation import (
    DynamicForcingInputError,
    _dataset_coverage,
    build_forcing_window,
    ecmwf_steps_for_window,
    validate_dynamic_request,
)


def test_validate_dynamic_request_accepts_black_sea_case():
    validate_dynamic_request(
        longitude=37.7691,
        latitude=44.724,
        hours=6,
        half_width_deg=1.0,
    )


def test_validate_dynamic_request_rejects_unsupported_horizon():
    with pytest.raises(
        DynamicForcingInputError
    ):
        validate_dynamic_request(
            longitude=37.7691,
            latitude=44.724,
            hours=18,
            half_width_deg=1.0,
        )


def test_build_forcing_window_clips_to_domain():
    window = build_forcing_window(
        longitude=41.8,
        latitude=46.8,
        at="2026-09-15T12:45:00+00:00",
        hours=6,
        half_width_deg=1.0,
    )

    assert window.start_time == datetime(
        2026,
        9,
        15,
        12,
        0,
        tzinfo=timezone.utc,
    )
    assert window.east <= 42.0
    assert window.north <= 47.0


def test_ecmwf_steps_bracket_non_three_hour_window():
    run = datetime(
        2026,
        9,
        15,
        6,
        tzinfo=timezone.utc,
    )
    start = datetime(
        2026,
        9,
        15,
        13,
        tzinfo=timezone.utc,
    )
    end = datetime(
        2026,
        9,
        15,
        19,
        tzinfo=timezone.utc,
    )

    assert ecmwf_steps_for_window(
        run_time=run,
        start_time=start,
        end_time=end,
    ) == (
        6,
        9,
        12,
        15,
    )


def test_ecmwf_steps_reject_beyond_supported_range():
    run = datetime(
        2026,
        9,
        15,
        0,
        tzinfo=timezone.utc,
    )
    start = datetime(
        2026,
        9,
        15,
        0,
        tzinfo=timezone.utc,
    )
    end = datetime(
        2026,
        9,
        22,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        DynamicForcingInputError
    ):
        ecmwf_steps_for_window(
            run_time=run,
            start_time=start,
            end_time=end,
        )


def test_dataset_coverage_accepts_complete_hourly_range():
    times = np.array([
        np.datetime64(
            "2026-09-15T12:00:00"
        ),
        np.datetime64(
            "2026-09-15T13:00:00"
        ),
        np.datetime64(
            "2026-09-15T14:00:00"
        ),
    ])

    dataset = xr.Dataset(
        data_vars={
            "uo": (
                (
                    "time",
                    "latitude",
                    "longitude",
                ),
                np.ones(
                    (
                        3,
                        1,
                        1,
                    )
                ),
            ),
            "vo": (
                (
                    "time",
                    "latitude",
                    "longitude",
                ),
                np.ones(
                    (
                        3,
                        1,
                        1,
                    )
                ),
            ),
        },
        coords={
            "time": times,
            "latitude": [44.7],
            "longitude": [37.8],
        },
    )

    coverage = _dataset_coverage(
        dataset,
        variables=(
            "uo",
            "vo",
        ),
        required_start=datetime(
            2026,
            9,
            15,
            12,
            tzinfo=timezone.utc,
        ),
        required_end=datetime(
            2026,
            9,
            15,
            14,
            tzinfo=timezone.utc,
        ),
    )

    assert coverage[
        "coverage_ok"
    ] is True
    assert coverage[
        "time_count"
    ] == 3


def test_dataset_coverage_detects_short_window():
    times = np.array([
        np.datetime64(
            "2026-09-15T12:00:00"
        ),
    ])

    dataset = xr.Dataset(
        data_vars={
            "thetao": (
                (
                    "time",
                    "latitude",
                    "longitude",
                ),
                np.ones(
                    (
                        1,
                        1,
                        1,
                    )
                ),
            ),
        },
        coords={
            "time": times,
            "latitude": [44.7],
            "longitude": [37.8],
        },
    )

    coverage = _dataset_coverage(
        dataset,
        variables=(
            "thetao",
        ),
        required_start=datetime(
            2026,
            9,
            15,
            12,
            tzinfo=timezone.utc,
        ),
        required_end=datetime(
            2026,
            9,
            15,
            18,
            tzinfo=timezone.utc,
        ),
    )

    assert coverage[
        "coverage_ok"
    ] is False


def test_dataset_coverage_counts_finite_values():
    dataset = xr.Dataset(
        data_vars={
            "so": (
                (
                    "time",
                    "latitude",
                    "longitude",
                ),
                np.array([
                    [
                        [18.0, np.nan]
                    ],
                    [
                        [18.1, 18.2]
                    ],
                ]),
            ),
        },
        coords={
            "time": [
                np.datetime64(
                    "2026-09-15T12:00:00"
                ),
                np.datetime64(
                    "2026-09-15T13:00:00"
                ),
            ],
            "latitude": [44.7],
            "longitude": [
                37.8,
                37.825,
            ],
        },
    )

    coverage = _dataset_coverage(
        dataset,
        variables=(
            "so",
        ),
        required_start=datetime(
            2026,
            9,
            15,
            12,
            tzinfo=timezone.utc,
        ),
        required_end=datetime(
            2026,
            9,
            15,
            13,
            tzinfo=timezone.utc,
        ),
    )

    assert coverage[
        "finite_counts"
    ][
        "so"
    ] == 3


def test_build_forcing_window_has_expected_duration():
    window = build_forcing_window(
        longitude=37.7691,
        latitude=44.724,
        at="2026-09-15T13:20:00+00:00",
        hours=12,
        half_width_deg=1.0,
    )

    assert (
        window.end_time
        - window.start_time
    ).total_seconds() == 12 * 3600



def test_copernicus_request_end_time_adds_interpolation_padding():
    from agents.ocean_data.dynamic_forcing_validation import (
        copernicus_request_end_time,
    )

    window = build_forcing_window(
        longitude=37.7691,
        latitude=44.724,
        at="2026-09-15T13:00:00+00:00",
        hours=6,
        half_width_deg=1.0,
    )

    assert (
        copernicus_request_end_time(
            window
        )
        == datetime(
            2026,
            9,
            15,
            20,
            0,
            tzinfo=timezone.utc,
        )
    )


def test_scientific_window_end_is_not_changed_by_padding():
    from agents.ocean_data.dynamic_forcing_validation import (
        copernicus_request_end_time,
    )

    window = build_forcing_window(
        longitude=37.7691,
        latitude=44.724,
        at="2026-09-15T13:00:00+00:00",
        hours=6,
        half_width_deg=1.0,
    )

    assert window.end_time == datetime(
        2026,
        9,
        15,
        19,
        0,
        tzinfo=timezone.utc,
    )
    assert copernicus_request_end_time(
        window
    ) > window.end_time
