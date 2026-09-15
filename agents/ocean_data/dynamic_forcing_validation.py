from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agents.ocean_data.environmental_forcing import (
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    SURFACE_DEPTH_M,
    EnvironmentalForcingError,
    EnvironmentalForcingInputError,
    normalize_target_time,
)


CURRENT_DATASET_ID = "cmems_mod_blk_phy-cur_anfc_2.5km_PT1H-m"
WAVE_DATASET_ID = "cmems_mod_blk_wav_anfc_2.5km_PT1H-i"
TEMPERATURE_DATASET_ID = "cmems_mod_blk_phy-temp_anfc_2.5km_PT1H-m"
SALINITY_DATASET_ID = "cmems_mod_blk_phy-sal_anfc_2.5km_PT1H-m"

CURRENT_VARIABLES = ("uo", "vo")
WAVE_VARIABLES = ("VHM0", "VSDX", "VSDY")
TEMPERATURE_VARIABLES = ("thetao",)
SALINITY_VARIABLES = ("so",)

SUPPORTED_HOURS = (6, 12, 24, 48, 72)

DEFAULT_HOURS = 6
DEFAULT_HALF_WIDTH_DEG = 1.0
COPERNICUS_END_PADDING_HOURS = 1

MIN_HALF_WIDTH_DEG = 0.25
MAX_HALF_WIDTH_DEG = 4.0

ECMWF_MAX_STEP_HOURS = 144
ECMWF_FILE_TTL_SECONDS = 3 * 60 * 60


class DynamicForcingError(RuntimeError):
    pass


class DynamicForcingInputError(ValueError):
    pass


@dataclass(frozen=True)
class ForcingWindow:
    start_time: datetime
    end_time: datetime
    west: float
    south: float
    east: float
    north: float


def validate_dynamic_request(
    *,
    longitude: float,
    latitude: float,
    hours: int,
    half_width_deg: float,
) -> None:
    if not (
        MIN_LONGITUDE
        <= float(longitude)
        <= MAX_LONGITUDE
    ):
        raise DynamicForcingInputError(
            "longitude is outside the Black Sea forcing domain."
        )

    if not (
        MIN_LATITUDE
        <= float(latitude)
        <= MAX_LATITUDE
    ):
        raise DynamicForcingInputError(
            "latitude is outside the Black Sea forcing domain."
        )

    if int(hours) not in SUPPORTED_HOURS:
        raise DynamicForcingInputError(
            "hours must be one of: "
            + ", ".join(
                str(value)
                for value in SUPPORTED_HOURS
            )
        )

    if not (
        MIN_HALF_WIDTH_DEG
        <= float(half_width_deg)
        <= MAX_HALF_WIDTH_DEG
    ):
        raise DynamicForcingInputError(
            "half_width_deg must be between "
            f"{MIN_HALF_WIDTH_DEG:g} and {MAX_HALF_WIDTH_DEG:g}."
        )


def build_forcing_window(
    *,
    longitude: float,
    latitude: float,
    at: str | datetime | None,
    hours: int,
    half_width_deg: float,
) -> ForcingWindow:
    validate_dynamic_request(
        longitude=longitude,
        latitude=latitude,
        hours=hours,
        half_width_deg=half_width_deg,
    )

    start_time = normalize_target_time(
        at
    )

    end_time = (
        start_time
        + timedelta(
            hours=int(hours)
        )
    )

    return ForcingWindow(
        start_time=start_time,
        end_time=end_time,
        west=max(
            MIN_LONGITUDE,
            float(longitude)
            - float(half_width_deg),
        ),
        south=max(
            MIN_LATITUDE,
            float(latitude)
            - float(half_width_deg),
        ),
        east=min(
            MAX_LONGITUDE,
            float(longitude)
            + float(half_width_deg),
        ),
        north=min(
            MAX_LATITUDE,
            float(latitude)
            + float(half_width_deg),
        ),
    )


def _iso_utc(
    value: Any,
) -> str:
    try:
        import numpy as np
    except ImportError:
        np = None

    if (
        np is not None
        and isinstance(
            value,
            np.datetime64,
        )
    ):
        if np.isnat(value):
            return str(value)

        nanoseconds = int(
            value.astype(
                "datetime64[ns]"
            ).astype(
                "int64"
            )
        )

        return datetime.fromtimestamp(
            nanoseconds
            / 1_000_000_000,
            tz=timezone.utc,
        ).isoformat()

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value)

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(
                text
            )
        except ValueError:
            return str(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )
    else:
        parsed = parsed.astimezone(
            timezone.utc
        )

    return parsed.isoformat()


def _as_utc_datetime(
    value: Any,
) -> datetime:
    text = _iso_utc(
        value
    )

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    parsed = datetime.fromisoformat(
        text
    )

    if parsed.tzinfo is None:
        return parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def ecmwf_steps_for_window(
    *,
    run_time: datetime,
    start_time: datetime,
    end_time: datetime,
    cadence_hours: int = 3,
    maximum_step_hours: int = ECMWF_MAX_STEP_HOURS,
) -> tuple[int, ...]:
    if cadence_hours <= 0:
        raise DynamicForcingInputError(
            "cadence_hours must be positive."
        )

    if run_time.tzinfo is None:
        run = run_time.replace(
            tzinfo=timezone.utc
        )
    else:
        run = run_time.astimezone(
            timezone.utc
        )

    start = (
        start_time
        if start_time.tzinfo is not None
        else start_time.replace(
            tzinfo=timezone.utc
        )
    ).astimezone(
        timezone.utc
    )

    end = (
        end_time
        if end_time.tzinfo is not None
        else end_time.replace(
            tzinfo=timezone.utc
        )
    ).astimezone(
        timezone.utc
    )

    if end < start:
        raise DynamicForcingInputError(
            "end_time must not be before start_time."
        )

    start_hours = (
        start - run
    ).total_seconds() / 3600.0

    end_hours = (
        end - run
    ).total_seconds() / 3600.0

    if end_hours < 0:
        raise DynamicForcingInputError(
            "ECMWF run is newer than the requested forcing window."
        )

    floor_step = (
        math.floor(
            max(0.0, start_hours)
            / cadence_hours
        )
        * cadence_hours
    )

    ceil_step = (
        math.ceil(
            max(0.0, end_hours)
            / cadence_hours
        )
        * cadence_hours
    )

    if ceil_step > maximum_step_hours:
        raise DynamicForcingInputError(
            "Requested forcing window exceeds supported ECMWF forecast step."
        )

    return tuple(
        range(
            int(floor_step),
            int(ceil_step)
            + cadence_hours,
            cadence_hours,
        )
    )


def _cache_root() -> Path:
    configured = os.getenv(
        "DYNAMIC_FORCING_CACHE_DIR"
    )

    if configured:
        return Path(configured)

    return (
        Path(tempfile.gettempdir())
        / "black-sea-eco-monitor"
        / "dynamic-forcing"
    )


def _coord_name(
    dataset,
    candidates: tuple[str, ...],
) -> str:
    for name in candidates:
        if (
            name in dataset.coords
            or name in dataset.dims
        ):
            return name

    raise DynamicForcingError(
        "Required coordinate not found: "
        + ", ".join(candidates)
    )


def _time_values(
    dataset,
) -> list[datetime]:
    if "time" not in dataset.coords:
        return []

    return [
        _as_utc_datetime(
            raw
        )
        for raw in (
            dataset["time"]
            .values
            .reshape(-1)
        )
    ]


def _dataset_coverage(
    dataset,
    *,
    variables: tuple[str, ...],
    required_start: datetime,
    required_end: datetime,
) -> dict:
    times = _time_values(
        dataset
    )

    missing_variables = [
        name
        for name in variables
        if name not in dataset
    ]

    if missing_variables:
        raise DynamicForcingError(
            "Dataset is missing variables: "
            + ", ".join(
                missing_variables
            )
        )

    if not times:
        raise DynamicForcingError(
            "Dataset has no time coordinate."
        )

    time_start = min(times)
    time_end = max(times)

    tolerance = timedelta(
        minutes=90
    )

    coverage_ok = (
        time_start
        <= required_start + tolerance
        and time_end
        >= required_end - tolerance
    )

    finite_counts = {}

    try:
        import numpy as np

        for name in variables:
            values = dataset[
                name
            ].values

            finite_counts[name] = int(
                np.isfinite(
                    values
                ).sum()
            )
    except Exception:
        finite_counts = {
            name: None
            for name in variables
        }

    return {
        "time_start": time_start.isoformat(),
        "time_end": time_end.isoformat(),
        "time_count": len(
            times
        ),
        "coverage_ok": coverage_ok,
        "finite_counts": finite_counts,
        "dimensions": {
            name: int(
                size
            )
            for name, size in (
                dataset.sizes.items()
            )
        },
    }



def copernicus_request_end_time(
    window: ForcingWindow,
) -> datetime:
    """
    OpenDrift readers interpolate in time and may need one forcing frame
    beyond the requested simulation end. Request one extra hourly frame
    from Copernicus while keeping the scientific forecast horizon unchanged.
    """
    return (
        window.end_time
        + timedelta(
            hours=COPERNICUS_END_PADDING_HOURS
        )
    )


def _open_copernicus_dynamic(
    *,
    dataset_id: str,
    variables: tuple[str, ...],
    window: ForcingWindow,
    include_depth: bool,
):
    try:
        import copernicusmarine
    except ImportError as exc:
        raise DynamicForcingError(
            "The 'copernicusmarine' package is not installed."
        ) from exc

    kwargs = {
        "dataset_id": dataset_id,
        "variables": list(
            variables
        ),
        "minimum_longitude": (
            window.west
        ),
        "maximum_longitude": (
            window.east
        ),
        "minimum_latitude": (
            window.south
        ),
        "maximum_latitude": (
            window.north
        ),
        "start_datetime": (
            window.start_time.isoformat()
        ),
        "end_datetime": (
            copernicus_request_end_time(
                window
            ).isoformat()
        ),
    }

    if include_depth:
        kwargs.update(
            {
                "minimum_depth": (
                    SURFACE_DEPTH_M
                ),
                "maximum_depth": (
                    SURFACE_DEPTH_M
                ),
            }
        )

    return copernicusmarine.open_dataset(
        **kwargs
    )


def _latest_ecmwf_client_and_run(
    target_time: datetime,
):
    try:
        from ecmwf.opendata import Client
    except ImportError as exc:
        raise DynamicForcingError(
            "The 'ecmwf-opendata' package is not installed."
        ) from exc

    client = Client(
        source="ecmwf",
        model="ifs",
    )

    latest = client.latest(
        stream="oper",
        type="fc",
        step=0,
        param="10u",
    )

    if latest.tzinfo is None:
        run_time = latest.replace(
            tzinfo=timezone.utc
        )
    else:
        run_time = latest.astimezone(
            timezone.utc
        )

    while run_time > target_time:
        run_time -= timedelta(
            hours=6
        )

    return (
        client,
        run_time,
    )


def _ecmwf_grib_path(
    run_time: datetime,
    step: int,
) -> Path:
    return (
        _cache_root()
        / "ecmwf"
        / (
            f"ifs_{run_time:%Y%m%dT%H}Z_"
            f"step{step:03d}_10u10v.grib2"
        )
    )


def _ecmwf_file_fresh(
    path: Path,
    ttl_seconds: int = ECMWF_FILE_TTL_SECONDS,
) -> bool:
    if not path.exists():
        return False

    age_seconds = (
        datetime.now(
            timezone.utc
        ).timestamp()
        - path.stat().st_mtime
    )

    return (
        age_seconds
        <= ttl_seconds
    )


def _download_ecmwf_steps(
    *,
    client,
    run_time: datetime,
    steps: tuple[int, ...],
) -> list[Path]:
    paths = []

    for step in steps:
        path = _ecmwf_grib_path(
            run_time,
            step,
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not _ecmwf_file_fresh(
            path
        ):
            client.retrieve(
                date=run_time.strftime(
                    "%Y-%m-%d"
                ),
                time=run_time.hour,
                stream="oper",
                type="fc",
                step=int(
                    step
                ),
                param=[
                    "10u",
                    "10v",
                ],
                target=str(
                    path
                ),
            )

        paths.append(
            path
        )

    return paths


def _slice_coordinate(
    values,
    minimum: float,
    maximum: float,
):
    first = float(
        values[0]
    )
    last = float(
        values[-1]
    )

    if first <= last:
        return slice(
            minimum,
            maximum,
        )

    return slice(
        maximum,
        minimum,
    )


def _open_ecmwf_wind_dataset(
    *,
    paths: list[Path],
    run_time: datetime,
    steps: tuple[int, ...],
    window: ForcingWindow,
):
    try:
        import numpy as np
        import xarray as xr
    except ImportError as exc:
        raise DynamicForcingError(
            "NumPy and xarray are required for ECMWF dynamic forcing."
        ) from exc

    frames = []

    for path, step in zip(
        paths,
        steps,
    ):
        dataset = xr.open_dataset(
            path,
            engine="cfgrib",
            backend_kwargs={
                "indexpath": "",
            },
        )

        try:
            lon_name = _coord_name(
                dataset,
                (
                    "longitude",
                    "lon",
                ),
            )
            lat_name = _coord_name(
                dataset,
                (
                    "latitude",
                    "lat",
                ),
            )

            u_name = next(
                (
                    name
                    for name in (
                        "u10",
                        "10u",
                    )
                    if name in dataset
                ),
                None,
            )
            v_name = next(
                (
                    name
                    for name in (
                        "v10",
                        "10v",
                    )
                    if name in dataset
                ),
                None,
            )

            if (
                u_name is None
                or v_name is None
            ):
                raise DynamicForcingError(
                    "ECMWF GRIB is missing u10/v10."
                )

            lon_values = dataset[
                lon_name
            ].values
            lat_values = dataset[
                lat_name
            ].values

            west = (
                window.west
                % 360.0
            )
            east = (
                window.east
                % 360.0
            )

            if east < west:
                raise DynamicForcingError(
                    "Dateline-crossing bbox is not supported in Black Sea forcing."
                )

            subset = dataset.sel(
                {
                    lon_name: (
                        _slice_coordinate(
                            lon_values,
                            west,
                            east,
                        )
                    ),
                    lat_name: (
                        _slice_coordinate(
                            lat_values,
                            window.south,
                            window.north,
                        )
                    ),
                }
            )

            u = subset[
                u_name
            ].squeeze(
                drop=True
            )
            v = subset[
                v_name
            ].squeeze(
                drop=True
            )

            frame = xr.Dataset(
                {
                    "x_wind": u,
                    "y_wind": v,
                }
            )

            valid_time = (
                run_time
                + timedelta(
                    hours=int(
                        step
                    )
                )
            )

            frame = frame.expand_dims(
                time=[
                    np.datetime64(
                        valid_time.replace(
                            tzinfo=None
                        )
                    )
                ]
            )

            frame = frame.load()

            frames.append(
                frame
            )
        finally:
            dataset.close()

    if not frames:
        raise DynamicForcingError(
            "No ECMWF wind frames were loaded."
        )

    combined = xr.concat(
        frames,
        dim="time",
    ).sortby(
        "time"
    )

    return combined


def _make_reader(
    dataset,
    *,
    name: str,
    mapping: dict[str, str] | None = None,
):
    try:
        from opendrift.readers import (
            reader_netCDF_CF_generic,
        )
    except ImportError as exc:
        raise DynamicForcingError(
            "OpenDrift is not installed."
        ) from exc

    kwargs = {
        "name": name,
    }

    if mapping:
        kwargs[
            "standard_name_mapping"
        ] = mapping

    return reader_netCDF_CF_generic.Reader(
        dataset,
        **kwargs,
    )


def validate_dynamic_forcing(
    *,
    longitude: float,
    latitude: float,
    at: str | datetime | None = None,
    hours: int = DEFAULT_HOURS,
    half_width_deg: float = DEFAULT_HALF_WIDTH_DEG,
) -> dict:
    window = build_forcing_window(
        longitude=longitude,
        latitude=latitude,
        at=at,
        hours=hours,
        half_width_deg=half_width_deg,
    )

    datasets = {}

    try:
        datasets["current"] = (
            _open_copernicus_dynamic(
                dataset_id=CURRENT_DATASET_ID,
                variables=CURRENT_VARIABLES,
                window=window,
                include_depth=True,
            )
        )

        datasets["wave"] = (
            _open_copernicus_dynamic(
                dataset_id=WAVE_DATASET_ID,
                variables=WAVE_VARIABLES,
                window=window,
                include_depth=False,
            )
        )

        datasets["temperature"] = (
            _open_copernicus_dynamic(
                dataset_id=TEMPERATURE_DATASET_ID,
                variables=TEMPERATURE_VARIABLES,
                window=window,
                include_depth=True,
            )
        )

        datasets["salinity"] = (
            _open_copernicus_dynamic(
                dataset_id=SALINITY_DATASET_ID,
                variables=SALINITY_VARIABLES,
                window=window,
                include_depth=True,
            )
        )

        ecmwf_client, run_time = (
            _latest_ecmwf_client_and_run(
                window.start_time
            )
        )

        steps = ecmwf_steps_for_window(
            run_time=run_time,
            start_time=window.start_time,
            end_time=window.end_time,
        )

        wind_paths = (
            _download_ecmwf_steps(
                client=ecmwf_client,
                run_time=run_time,
                steps=steps,
            )
        )

        datasets["wind"] = (
            _open_ecmwf_wind_dataset(
                paths=wind_paths,
                run_time=run_time,
                steps=steps,
                window=window,
            )
        )

        coverage = {
            "current": _dataset_coverage(
                datasets["current"],
                variables=CURRENT_VARIABLES,
                required_start=window.start_time,
                required_end=window.end_time,
            ),
            "wave": _dataset_coverage(
                datasets["wave"],
                variables=WAVE_VARIABLES,
                required_start=window.start_time,
                required_end=window.end_time,
            ),
            "temperature": _dataset_coverage(
                datasets["temperature"],
                variables=TEMPERATURE_VARIABLES,
                required_start=window.start_time,
                required_end=window.end_time,
            ),
            "salinity": _dataset_coverage(
                datasets["salinity"],
                variables=SALINITY_VARIABLES,
                required_start=window.start_time,
                required_end=window.end_time,
            ),
            "wind": _dataset_coverage(
                datasets["wind"],
                variables=(
                    "x_wind",
                    "y_wind",
                ),
                required_start=window.start_time,
                required_end=window.end_time,
            ),
        }

        readers = {
            "current": _make_reader(
                datasets["current"],
                name="Black Sea dynamic currents",
                mapping={
                    "uo": "x_sea_water_velocity",
                    "vo": "y_sea_water_velocity",
                },
            ),
            "wave": _make_reader(
                datasets["wave"],
                name="Black Sea dynamic waves",
                mapping={
                    "VHM0": "sea_surface_wave_significant_height",
                    "VSDX": "sea_surface_wave_stokes_drift_x_velocity",
                    "VSDY": "sea_surface_wave_stokes_drift_y_velocity",
                },
            ),
            "temperature": _make_reader(
                datasets["temperature"],
                name="Black Sea dynamic temperature",
                mapping={
                    "thetao": "sea_water_temperature",
                },
            ),
            "salinity": _make_reader(
                datasets["salinity"],
                name="Black Sea dynamic salinity",
                mapping={
                    "so": "sea_water_salinity",
                },
            ),
            "wind": _make_reader(
                datasets["wind"],
                name="ECMWF dynamic wind",
            ),
        }

        reader_summary = {}

        for key, reader in (
            readers.items()
        ):
            variables = sorted(
                str(value)
                for value in getattr(
                    reader,
                    "variables",
                    []
                )
            )

            reader_summary[key] = {
                "created": True,
                "variables": variables,
                "start_time": (
                    None
                    if getattr(
                        reader,
                        "start_time",
                        None,
                    )
                    is None
                    else _iso_utc(
                        reader.start_time
                    )
                ),
                "end_time": (
                    None
                    if getattr(
                        reader,
                        "end_time",
                        None,
                    )
                    is None
                    else _iso_utc(
                        reader.end_time
                    )
                ),
            }

        all_coverage_ok = all(
            item[
                "coverage_ok"
            ]
            for item in (
                coverage.values()
            )
        )

        return {
            "mode": (
                "openoil_dynamic_forcing_validation"
            ),
            "ready_for_dynamic_openoil": (
                all_coverage_ok
                and all(
                    item[
                        "created"
                    ]
                    for item in (
                        reader_summary.values()
                    )
                )
            ),
            "requested_location": {
                "longitude": round(
                    float(
                        longitude
                    ),
                    6,
                ),
                "latitude": round(
                    float(
                        latitude
                    ),
                    6,
                ),
            },
            "window": {
                "start_time": (
                    window.start_time.isoformat()
                ),
                "end_time": (
                    window.end_time.isoformat()
                ),
                "copernicus_request_end_time": (
                    copernicus_request_end_time(
                        window
                    ).isoformat()
                ),
                "copernicus_end_padding_hours": (
                    COPERNICUS_END_PADDING_HOURS
                ),
                "hours": int(
                    hours
                ),
                "bbox": {
                    "west": window.west,
                    "south": window.south,
                    "east": window.east,
                    "north": window.north,
                },
            },
            "datasets": {
                "current": {
                    "dataset_id": CURRENT_DATASET_ID,
                    **coverage[
                        "current"
                    ],
                },
                "wave": {
                    "dataset_id": WAVE_DATASET_ID,
                    **coverage[
                        "wave"
                    ],
                },
                "temperature": {
                    "dataset_id": TEMPERATURE_DATASET_ID,
                    **coverage[
                        "temperature"
                    ],
                },
                "salinity": {
                    "dataset_id": SALINITY_DATASET_ID,
                    **coverage[
                        "salinity"
                    ],
                },
                "wind": {
                    "source": "ECMWF IFS Open Data",
                    "run_time": (
                        run_time.isoformat()
                    ),
                    "steps": list(
                        steps
                    ),
                    **coverage[
                        "wind"
                    ],
                },
            },
            "readers": reader_summary,
        }

    except (
        DynamicForcingInputError,
        DynamicForcingError,
        EnvironmentalForcingInputError,
        EnvironmentalForcingError,
    ):
        raise
    except Exception as exc:
        raise DynamicForcingError(
            "Dynamic forcing validation failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    finally:
        for dataset in (
            datasets.values()
        ):
            if hasattr(
                dataset,
                "close",
            ):
                try:
                    dataset.close()
                except Exception:
                    pass
