import numpy as np
import xarray as xr

from backend.services.cams_netcdf_inspection import (
    inspect_dataset_object,
)


def test_inspection_detects_grid_axes_and_variable_stats():
    dataset = xr.Dataset(
        data_vars={
            "pm25_conc": (
                (
                    "time",
                    "latitude",
                    "longitude",
                ),
                np.array(
                    [
                        [
                            [1.0, 2.0],
                            [3.0, 4.0],
                        ],
                        [
                            [2.0, 3.0],
                            [4.0, 5.0],
                        ],
                    ]
                ),
                {
                    "units": "µg/m3",
                    "long_name": "PM2.5",
                },
            ),
        },
        coords={
            "time": np.array(
                [
                    "2026-09-19T00:00:00",
                    "2026-09-19T06:00:00",
                ],
                dtype="datetime64[ns]",
            ),
            "latitude": np.array(
                [48.0, 47.9]
            ),
            "longitude": np.array(
                [26.0, 26.1]
            ),
        },
    )

    result = inspect_dataset_object(
        dataset
    )

    assert result["dims"] == {
        "time": 2,
        "latitude": 2,
        "longitude": 2,
    }

    assert result["detected_axes"] == {
        "latitude": "latitude",
        "longitude": "longitude",
        "time": "time",
        "level": None,
    }

    assert (
        result["coordinates"][
            "latitude"
        ]["orientation"]
        == "descending"
    )

    assert (
        result["coordinates"][
            "longitude"
        ]["orientation"]
        == "ascending"
    )

    variable = result[
        "data_variables"
    ]["pm25_conc"]

    assert variable["min"] == 1.0
    assert variable["max"] == 5.0
    assert variable["mean"] == 3.0
    assert variable["attrs"][
        "units"
    ] == "µg/m3"
