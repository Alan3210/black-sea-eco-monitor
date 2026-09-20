from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr


LAT_CANDIDATES = ("latitude", "lat")
LON_CANDIDATES = ("longitude", "lon")
TIME_CANDIDATES = (
    "time",
    "valid_time",
    "forecast_time",
    "forecast_period",
    "leadtime",
    "step",
)
LEVEL_CANDIDATES = (
    "level",
    "height",
    "surface",
)


def _json_value(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()

    if isinstance(
        value,
        np.datetime64,
    ):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, (list, tuple)):
        return [
            _json_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key): _json_value(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (str, int, float, bool),
    ) or value is None:
        return value

    return str(value)


def _attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    return {
        str(key): _json_value(value)
        for key, value in attrs.items()
    }


def _first_last(values: np.ndarray) -> tuple[Any, Any]:
    flat = np.asarray(values).reshape(-1)

    if flat.size == 0:
        return None, None

    return (
        _json_value(flat[0]),
        _json_value(flat[-1]),
    )


def _orientation(values: np.ndarray) -> str | None:
    flat = np.asarray(values).reshape(-1)

    if flat.size < 2:
        return None

    if np.issubdtype(
        flat.dtype,
        np.datetime64,
    ):
        numeric = flat.astype(
            "datetime64[ns]"
        ).astype("int64")
    elif np.issubdtype(
        flat.dtype,
        np.number,
    ):
        numeric = flat.astype(float)
    else:
        return None

    delta = np.diff(numeric)

    if np.all(delta > 0):
        return "ascending"

    if np.all(delta < 0):
        return "descending"

    return "non_monotonic"


def _coord_summary(
    coord: xr.DataArray,
) -> dict[str, Any]:
    values = np.asarray(coord.values)
    first, last = _first_last(values)

    result = {
        "dims": list(coord.dims),
        "shape": list(coord.shape),
        "dtype": str(coord.dtype),
        "attrs": _attrs(dict(coord.attrs)),
        "first": first,
        "last": last,
        "orientation": (
            _orientation(values)
            if coord.ndim == 1
            else None
        ),
    }

    if coord.ndim == 1 and coord.size <= 24:
        result["values"] = [
            _json_value(item)
            for item in values.tolist()
        ]

    return result


def _numeric_stats(
    array: xr.DataArray,
) -> dict[str, Any]:
    if not np.issubdtype(
        array.dtype,
        np.number,
    ):
        return {}

    values = np.asarray(
        array.values
    )

    finite = np.isfinite(values)

    if not finite.any():
        return {
            "finite_count": 0,
            "nan_count": int(
                values.size
            ),
            "min": None,
            "max": None,
            "mean": None,
        }

    selected = values[finite]

    return {
        "finite_count": int(
            finite.sum()
        ),
        "nan_count": int(
            values.size
            - finite.sum()
        ),
        "min": float(
            np.min(selected)
        ),
        "max": float(
            np.max(selected)
        ),
        "mean": float(
            np.mean(selected)
        ),
    }


def _variable_summary(
    array: xr.DataArray,
) -> dict[str, Any]:
    result = {
        "dims": list(array.dims),
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "attrs": _attrs(
            dict(array.attrs)
        ),
    }

    result.update(
        _numeric_stats(array)
    )

    return result


def _find_first(
    names: tuple[str, ...],
    dataset: xr.Dataset,
) -> str | None:
    lower_to_actual = {
        name.lower(): name
        for name in (
            list(dataset.coords)
            + list(dataset.dims)
        )
    }

    for candidate in names:
        if candidate in lower_to_actual:
            return lower_to_actual[
                candidate
            ]

    return None


def inspect_dataset_object(
    dataset: xr.Dataset,
) -> dict[str, Any]:
    lat_name = _find_first(
        LAT_CANDIDATES,
        dataset,
    )
    lon_name = _find_first(
        LON_CANDIDATES,
        dataset,
    )
    time_name = _find_first(
        TIME_CANDIDATES,
        dataset,
    )
    level_name = _find_first(
        LEVEL_CANDIDATES,
        dataset,
    )

    return {
        "dims": {
            str(name): int(size)
            for name, size
            in dataset.sizes.items()
        },
        "coordinates": {
            str(name):
                _coord_summary(
                    dataset.coords[name]
                )
            for name in dataset.coords
        },
        "data_variables": {
            str(name):
                _variable_summary(
                    dataset[name]
                )
            for name in dataset.data_vars
        },
        "global_attrs": _attrs(
            dict(dataset.attrs)
        ),
        "detected_axes": {
            "latitude": lat_name,
            "longitude": lon_name,
            "time": time_name,
            "level": level_name,
        },
    }


def inspect_netcdf(
    path: Path | str,
) -> dict[str, Any]:
    netcdf_path = Path(path)

    if not netcdf_path.exists():
        raise FileNotFoundError(
            netcdf_path
        )

    try:
        dataset = xr.open_dataset(
            netcdf_path
        )
    except Exception:
        dataset = xr.open_dataset(
            netcdf_path,
            decode_times=False,
        )

    try:
        result = inspect_dataset_object(
            dataset
        )
    finally:
        dataset.close()

    result["path"] = str(
        netcdf_path
    )

    result["file_size_bytes"] = int(
        netcdf_path.stat().st_size
    )

    return result


def write_inspection_json(
    inspection: dict[str, Any],
    output_path: Path | str,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            inspection,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path
