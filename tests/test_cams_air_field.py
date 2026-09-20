from datetime import date
from pathlib import Path

import numpy as np
import xarray as xr

from backend.services.cams_air_field import (
    detect_pollutant_variable,
    extract_canonical_air_field,
    operational_lead_hour,
)


def _write_realistic_cams_file(
    path: Path,
):
    dataset = xr.Dataset(
        data_vars={
            "pm2p5_conc": (
                (
                    "time",
                    "level",
                    "latitude",
                    "longitude",
                ),
                np.arange(
                    3 * 1 * 4 * 5,
                    dtype=np.float32,
                ).reshape(
                    3,
                    1,
                    4,
                    5,
                ),
                {
                    "species":
                        "PM2.5 Aerosol",
                    "standard_name":
                        "mass_concentration_of_pm2p5_ambient_aerosol_in_air",
                    "units":
                        "µg/m3",
                },
            ),
            "no2_conc": (
                (
                    "time",
                    "level",
                    "latitude",
                    "longitude",
                ),
                np.ones(
                    (
                        3,
                        1,
                        4,
                        5,
                    ),
                    dtype=np.float32,
                ),
                {
                    "species":
                        "Nitrogen Dioxide",
                    "standard_name":
                        "mass_concentration_of_nitrogen_dioxide_in_air",
                    "units":
                        "µg/m3",
                },
            ),
        },
        coords={
            "time":
                np.array(
                    [
                        0.0,
                        6.0,
                        12.0,
                    ],
                    dtype=np.float32,
                ),
            "level":
                np.array(
                    [0.0],
                    dtype=np.float32,
                ),
            "latitude":
                np.array(
                    [
                        48.0,
                        47.9,
                        47.8,
                        47.7,
                    ],
                    dtype=np.float32,
                ),
            "longitude":
                np.array(
                    [
                        26.0,
                        26.1,
                        26.2,
                        26.3,
                        26.4,
                    ],
                    dtype=np.float32,
                ),
        },
    )

    dataset["time"].attrs[
        "units"
    ] = "hours"

    dataset["level"].attrs[
        "units"
    ] = "m"

    dataset.to_netcdf(
        path
    )


def test_detects_real_cams_pollutant_variable(
    tmp_path,
):
    path = (
        tmp_path
        / "ENS_FORECAST.nc"
    )

    _write_realistic_cams_file(
        path
    )

    dataset = xr.open_dataset(
        path
    )

    try:
        assert (
            detect_pollutant_variable(
                dataset,
                "pm25",
            )
            == "pm2p5_conc"
        )
    finally:
        dataset.close()


def test_extracts_canonical_grid_and_flips_latitude(
    tmp_path,
):
    path = (
        tmp_path
        / "ENS_FORECAST.nc"
    )

    _write_realistic_cams_file(
        path
    )

    field = (
        extract_canonical_air_field(
            netcdf_path=path,
            pollutant="pm25",
            run_date="2026-09-19",
            lead_hour=6,
            stride=2,
        )
    )

    assert field[
        "semantics"
    ]["kind"] == (
        "model_forecast"
    )

    assert field[
        "pollutant"
    ]["source_variable"] == (
        "pm2p5_conc"
    )

    assert field[
        "pollutant"
    ]["units"] == "µg/m3"

    assert field[
        "valid_time"
    ] == (
        "2026-09-19T06:00:00+00:00"
    )

    assert field[
        "grid"
    ]["latitude_order"] == (
        "ascending"
    )

    assert field[
        "grid"
    ]["longitude_order"] == (
        "ascending"
    )

    assert field[
        "grid"
    ]["shape"] == [
        2,
        3,
    ]

    assert (
        field["grid"][
            "latitudes"
        ][0]
        < field["grid"][
            "latitudes"
        ][-1]
    )


def test_operational_lead_hour_is_clamped():
    from datetime import datetime, timezone

    assert (
        operational_lead_hour(
            date(
                2026,
                9,
                19,
            ),
            datetime(
                2026,
                9,
                20,
                5,
                30,
                tzinfo=timezone.utc,
            ),
        )
        == 29
    )
