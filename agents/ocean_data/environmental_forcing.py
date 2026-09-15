from __future__ import annotations

import json
import math
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------
# Copernicus Marine products used by the Black Sea Eco Monitor
# ---------------------------------------------------------------------

CURRENT_DATASET_ID = "cmems_mod_blk_phy-cur_anfc_2.5km_PT1H-m"
WAVE_DATASET_ID = "cmems_mod_blk_wav_anfc_2.5km_PT1H-i"

CURRENT_VARIABLES = ("uo", "vo")
WAVE_VARIABLES = ("VHM0", "VSDX", "VSDY")

SURFACE_DEPTH_M = 0.5001727938652039

MIN_LONGITUDE = 27.25
MAX_LONGITUDE = 42.0
MIN_LATITUDE = 40.5
MAX_LATITUDE = 47.0

DEFAULT_CACHE_TTL_SECONDS = 15 * 60
DEFAULT_ECMWF_FILE_TTL_SECONDS = 3 * 60 * 60
POINT_PADDING_DEG = 0.20
MAX_COPERNICUS_SAMPLE_DISTANCE_KM = 30.0


class EnvironmentalForcingError(RuntimeError):
    pass


class EnvironmentalForcingInputError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_target_time(
    value: str | datetime | None,
) -> datetime:
    if value is None:
        parsed = utc_now()
    elif isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise EnvironmentalForcingInputError(
                "at must be an ISO 8601 datetime."
            ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    # Copernicus Black Sea current/wave products are hourly.
    return parsed.replace(
        minute=0,
        second=0,
        microsecond=0,
    )


def validate_location(
    longitude: float,
    latitude: float,
) -> None:
    if not (
        MIN_LONGITUDE
        <= float(longitude)
        <= MAX_LONGITUDE
    ):
        raise EnvironmentalForcingInputError(
            "longitude is outside the Black Sea forcing domain."
        )

    if not (
        MIN_LATITUDE
        <= float(latitude)
        <= MAX_LATITUDE
    ):
        raise EnvironmentalForcingInputError(
            "latitude is outside the Black Sea forcing domain."
        )


def vector_speed(
    u: float,
    v: float,
) -> float:
    return math.hypot(
        float(u),
        float(v),
    )


def direction_to_deg(
    u: float,
    v: float,
) -> float | None:
    speed = vector_speed(u, v)

    if speed <= 1e-12:
        return None

    return (
        math.degrees(
            math.atan2(
                float(u),
                float(v),
            )
        )
        + 360.0
    ) % 360.0


def direction_from_deg(
    u: float,
    v: float,
) -> float | None:
    direction = direction_to_deg(
        u,
        v,
    )

    if direction is None:
        return None

    return (
        direction + 180.0
    ) % 360.0


def nearest_three_hour_step(
    target_time: datetime,
    run_time: datetime,
    *,
    maximum_step: int = 144,
) -> int:
    target = normalize_target_time(
        target_time
    )

    if run_time.tzinfo is None:
        run = run_time.replace(
            tzinfo=timezone.utc
        )
    else:
        run = run_time.astimezone(
            timezone.utc
        )

    raw_hours = (
        target - run
    ).total_seconds() / 3600.0

    if raw_hours < 0:
        raise EnvironmentalForcingInputError(
            "ECMWF forecast run is newer than the requested time."
        )

    rounded = int(
        round(raw_hours / 3.0)
        * 3
    )

    return max(
        0,
        min(
            maximum_step,
            rounded,
        ),
    )


def _cache_root() -> Path:
    configured = os.getenv(
        "ENVIRONMENTAL_FORCING_CACHE_DIR"
    )

    if configured:
        return Path(configured)

    return (
        Path(tempfile.gettempdir())
        / "black-sea-eco-monitor"
        / "environmental-forcing"
    )


def _combined_cache_path(
    longitude: float,
    latitude: float,
    target_time: datetime,
) -> Path:
    key = (
        f"{target_time:%Y%m%dT%H00Z}_"
        f"{longitude:.4f}_"
        f"{latitude:.4f}"
    )

    safe = key.replace("-", "m")

    return (
        _cache_root()
        / f"forcing_{safe}.json"
    )


def _read_json_cache(
    path: Path,
    ttl_seconds: int,
) -> dict | None:
    if not path.exists():
        return None

    age = (
        utc_now().timestamp()
        - path.stat().st_mtime
    )

    if age > ttl_seconds:
        return None

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None


def _write_json_cache(
    path: Path,
    payload: dict,
) -> None:
    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
    except OSError:
        # Cache is an optimisation only.
        pass


def _iso_utc(
    value: Any,
) -> str:
    """
    Convert datetime-like values to an offset-aware UTC ISO 8601 string.

    Important: ``numpy.datetime64.item()`` may return an integer number of
    nanoseconds for ns-resolution values. Handle numpy datetime64 before
    calling ``item()`` so valid model times do not leak into API/log output as
    values such as ``1789473600000000000``.
    """
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

        parsed = datetime.fromtimestamp(
            nanoseconds / 1_000_000_000,
            tz=timezone.utc,
        )

        return parsed.isoformat()

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, datetime):
        parsed = value
    elif (
        isinstance(
            value,
            int,
        )
        and abs(value) >= 10**17
    ):
        # Defensive compatibility for already-unwrapped ns timestamps.
        parsed = datetime.fromtimestamp(
            value / 1_000_000_000,
            tz=timezone.utc,
        )
    else:
        raw_text = str(value)

        if raw_text.endswith("Z"):
            raw_text = (
                raw_text[:-1]
                + "+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                raw_text
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

    raise EnvironmentalForcingError(
        "Required coordinate not found: "
        + ", ".join(candidates)
    )


def _scalar(
    data_array,
) -> float:
    values = data_array.values

    try:
        value = values.item()
    except ValueError:
        value = values.reshape(-1)[0]

    number = float(value)

    if not math.isfinite(number):
        raise EnvironmentalForcingError(
            "Forcing field contains a non-finite value."
        )

    return number



def _haversine_km(
    longitude_a: float,
    latitude_a: float,
    longitude_b: float,
    latitude_b: float,
) -> float:
    radius_km = 6371.0088

    lat1 = math.radians(latitude_a)
    lat2 = math.radians(latitude_b)
    delta_lat = math.radians(
        latitude_b - latitude_a
    )
    delta_lon = math.radians(
        longitude_b - longitude_a
    )

    haversine = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2.0) ** 2
    )

    return (
        2.0
        * radius_km
        * math.asin(
            min(
                1.0,
                math.sqrt(haversine),
            )
        )
    )


def _point_from_dataset(
    dataset,
    *,
    longitude: float,
    latitude: float,
    variable_names: tuple[str, ...],
) -> tuple[dict[str, float], str | None, dict]:
    """
    Sample the nearest grid cell where every requested variable is finite.

    This matters on the Black Sea coast: Copernicus ocean grids mask land
    cells with NaN. A plain xarray ``sel(..., method="nearest")`` may choose
    a coastal land cell even though valid water cells exist a few kilometres
    away.
    """
    try:
        import numpy as np
    except ImportError as exc:
        raise EnvironmentalForcingError(
            "NumPy is required for Copernicus forcing sampling."
        ) from exc

    longitude_name = _coord_name(
        dataset,
        ("longitude", "lon"),
    )
    latitude_name = _coord_name(
        dataset,
        ("latitude", "lat"),
    )

    working = dataset

    # Keep scalar time/depth coordinates while removing those dimensions.
    for dimension in (
        "time",
        "depth",
    ):
        if (
            dimension in working.dims
            and working.sizes[
                dimension
            ] >= 1
        ):
            working = working.isel(
                {
                    dimension: 0
                }
            )

    for name in variable_names:
        if name not in working:
            raise EnvironmentalForcingError(
                f"Variable '{name}' is missing from dataset."
            )

    longitude_values = np.asarray(
        working[longitude_name].values,
        dtype=float,
    )
    latitude_values = np.asarray(
        working[latitude_name].values,
        dtype=float,
    )

    if (
        longitude_values.ndim != 1
        or latitude_values.ndim != 1
    ):
        raise EnvironmentalForcingError(
            "Copernicus forcing sampler currently expects "
            "1D longitude/latitude coordinates."
        )

    valid = np.ones(
        (
            latitude_values.size,
            longitude_values.size,
        ),
        dtype=bool,
    )

    normalized_arrays = {}

    for name in variable_names:
        array = working[name].squeeze(
            drop=True
        )

        extra_dimensions = [
            dimension
            for dimension in array.dims
            if dimension
            not in (
                latitude_name,
                longitude_name,
            )
        ]

        if extra_dimensions:
            raise EnvironmentalForcingError(
                f"Variable '{name}' has unsupported dimensions: "
                + ", ".join(
                    extra_dimensions
                )
            )

        array = array.transpose(
            latitude_name,
            longitude_name,
        )

        values = np.asarray(
            array.values,
            dtype=float,
        )

        if values.shape != valid.shape:
            raise EnvironmentalForcingError(
                f"Variable '{name}' has unexpected grid shape."
            )

        normalized_arrays[name] = values
        valid &= np.isfinite(
            values
        )

    if not valid.any():
        raise EnvironmentalForcingError(
            "No finite ocean forcing cell was found near "
            f"{longitude:.5f}, {latitude:.5f}. "
            "The requested point may be on land or outside the "
            "available ocean mask."
        )

    longitude_grid, latitude_grid = np.meshgrid(
        longitude_values,
        latitude_values,
    )

    longitude_scale = max(
        0.1,
        math.cos(
            math.radians(
                latitude
            )
        ),
    )

    distance_squared = (
        (
            (
                longitude_grid
                - float(longitude)
            )
            * longitude_scale
        )
        ** 2
        + (
            latitude_grid
            - float(latitude)
        )
        ** 2
    )

    distance_squared = np.where(
        valid,
        distance_squared,
        np.inf,
    )

    flat_index = int(
        np.argmin(
            distance_squared
        )
    )

    latitude_index, longitude_index = (
        np.unravel_index(
            flat_index,
            distance_squared.shape,
        )
    )

    sampled_longitude = float(
        longitude_values[
            longitude_index
        ]
    )
    sampled_latitude = float(
        latitude_values[
            latitude_index
        ]
    )

    sample_distance_km = _haversine_km(
        float(longitude),
        float(latitude),
        sampled_longitude,
        sampled_latitude,
    )

    if (
        sample_distance_km
        > MAX_COPERNICUS_SAMPLE_DISTANCE_KM
    ):
        raise EnvironmentalForcingError(
            "Nearest finite ocean forcing cell is too far from "
            f"the requested point ({sample_distance_km:.1f} km)."
        )

    values = {
        name: float(
            normalized_arrays[name][
                latitude_index,
                longitude_index,
            ]
        )
        for name in variable_names
    }

    valid_time = None

    if "time" in working.coords:
        valid_time = _iso_utc(
            working["time"].values
        )

    sampled_location = {
        "longitude": round(
            sampled_longitude,
            6,
        ),
        "latitude": round(
            sampled_latitude,
            6,
        ),
        "distance_km": round(
            sample_distance_km,
            3,
        ),
        "method": (
            "nearest_finite_ocean_cell"
        ),
    }

    return (
        values,
        valid_time,
        sampled_location,
    )

def _open_copernicus_point_dataset(
    *,
    dataset_id: str,
    variables: tuple[str, ...],
    longitude: float,
    latitude: float,
    target_time: datetime,
    include_depth: bool = False,
):
    try:
        import copernicusmarine
    except ImportError as exc:
        raise EnvironmentalForcingError(
            "The 'copernicusmarine' package is not installed."
        ) from exc

    minimum_longitude = max(
        MIN_LONGITUDE,
        longitude - POINT_PADDING_DEG,
    )
    maximum_longitude = min(
        MAX_LONGITUDE,
        longitude + POINT_PADDING_DEG,
    )
    minimum_latitude = max(
        MIN_LATITUDE,
        latitude - POINT_PADDING_DEG,
    )
    maximum_latitude = min(
        MAX_LATITUDE,
        latitude + POINT_PADDING_DEG,
    )

    kwargs = {
        "dataset_id": dataset_id,
        "variables": list(
            variables
        ),
        "minimum_longitude": (
            minimum_longitude
        ),
        "maximum_longitude": (
            maximum_longitude
        ),
        "minimum_latitude": (
            minimum_latitude
        ),
        "maximum_latitude": (
            maximum_latitude
        ),
        "start_datetime": (
            target_time.isoformat()
        ),
        "end_datetime": (
            target_time.isoformat()
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


def fetch_current_at_point(
    *,
    longitude: float,
    latitude: float,
    target_time: datetime,
) -> dict:
    dataset = None

    try:
        dataset = _open_copernicus_point_dataset(
            dataset_id=CURRENT_DATASET_ID,
            variables=CURRENT_VARIABLES,
            longitude=longitude,
            latitude=latitude,
            target_time=target_time,
            include_depth=True,
        )

        values, valid_time, sampled = (
            _point_from_dataset(
                dataset,
                longitude=longitude,
                latitude=latitude,
                variable_names=CURRENT_VARIABLES,
            )
        )

        u = values["uo"]
        v = values["vo"]

        return {
            "source": "Copernicus Marine",
            "dataset_id": CURRENT_DATASET_ID,
            "valid_time": valid_time,
            "sampled_location": sampled,
            "depth_m": SURFACE_DEPTH_M,
            "u_m_s": round(
                u,
                6,
            ),
            "v_m_s": round(
                v,
                6,
            ),
            "speed_m_s": round(
                vector_speed(
                    u,
                    v,
                ),
                6,
            ),
            "direction_to_deg": (
                None
                if direction_to_deg(
                    u,
                    v,
                )
                is None
                else round(
                    direction_to_deg(
                        u,
                        v,
                    ),
                    2,
                )
            ),
        }
    finally:
        if (
            dataset is not None
            and hasattr(
                dataset,
                "close",
            )
        ):
            dataset.close()


def fetch_wave_at_point(
    *,
    longitude: float,
    latitude: float,
    target_time: datetime,
) -> dict:
    dataset = None

    try:
        dataset = _open_copernicus_point_dataset(
            dataset_id=WAVE_DATASET_ID,
            variables=WAVE_VARIABLES,
            longitude=longitude,
            latitude=latitude,
            target_time=target_time,
            include_depth=False,
        )

        values, valid_time, sampled = (
            _point_from_dataset(
                dataset,
                longitude=longitude,
                latitude=latitude,
                variable_names=WAVE_VARIABLES,
            )
        )

        stokes_u = values["VSDX"]
        stokes_v = values["VSDY"]

        return {
            "source": "Copernicus Marine",
            "dataset_id": WAVE_DATASET_ID,
            "valid_time": valid_time,
            "sampled_location": sampled,
            "significant_wave_height_m": round(
                values["VHM0"],
                4,
            ),
            "stokes_u_m_s": round(
                stokes_u,
                6,
            ),
            "stokes_v_m_s": round(
                stokes_v,
                6,
            ),
            "stokes_speed_m_s": round(
                vector_speed(
                    stokes_u,
                    stokes_v,
                ),
                6,
            ),
            "stokes_direction_to_deg": (
                None
                if direction_to_deg(
                    stokes_u,
                    stokes_v,
                )
                is None
                else round(
                    direction_to_deg(
                        stokes_u,
                        stokes_v,
                    ),
                    2,
                )
            ),
        }
    finally:
        if (
            dataset is not None
            and hasattr(
                dataset,
                "close",
            )
        ):
            dataset.close()


def _ecmwf_grib_path(
    run_time: datetime,
    step_hours: int,
) -> Path:
    return (
        _cache_root()
        / "ecmwf"
        / (
            f"ifs_{run_time:%Y%m%dT%H}Z_"
            f"step{step_hours:03d}_"
            "10u10v.grib2"
        )
    )


def _ecmwf_file_fresh(
    path: Path,
    ttl_seconds: int,
) -> bool:
    if not path.exists():
        return False

    return (
        utc_now().timestamp()
        - path.stat().st_mtime
    ) <= ttl_seconds


def _latest_ecmwf_run(
):
    try:
        from ecmwf.opendata import Client
    except ImportError as exc:
        raise EnvironmentalForcingError(
            "The 'ecmwf-opendata' package is not installed."
        ) from exc

    client = Client(
        source="ecmwf",
        model="ifs",
    )

    run_time = client.latest(
        stream="oper",
        type="fc",
        step=0,
        param="10u",
    )

    if run_time.tzinfo is None:
        run_time = run_time.replace(
            tzinfo=timezone.utc
        )
    else:
        run_time = run_time.astimezone(
            timezone.utc
        )

    return client, run_time


def _download_ecmwf_wind(
    *,
    target_time: datetime,
    ttl_seconds: int,
) -> tuple[Path, datetime, int]:
    client, run_time = (
        _latest_ecmwf_run()
    )

    # If a newly published run is later than the requested hour,
    # fall back by 6h increments. Operational IFS cycles are 00/06/12/18.
    while target_time < run_time:
        run_time -= timedelta(
            hours=6
        )

    step_hours = nearest_three_hour_step(
        target_time,
        run_time,
        maximum_step=144,
    )

    path = _ecmwf_grib_path(
        run_time,
        step_hours,
    )

    if _ecmwf_file_fresh(
        path,
        ttl_seconds,
    ):
        return (
            path,
            run_time,
            step_hours,
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    client.retrieve(
        date=run_time.strftime(
            "%Y-%m-%d"
        ),
        time=run_time.hour,
        stream="oper",
        type="fc",
        step=step_hours,
        param=["10u", "10v"],
        target=str(path),
    )

    return (
        path,
        run_time,
        step_hours,
    )


def _cfgrib_wind_point(
    path: Path,
    *,
    longitude: float,
    latitude: float,
) -> tuple[float, float, dict]:
    try:
        import xarray as xr
    except ImportError as exc:
        raise EnvironmentalForcingError(
            "The 'xarray' package is not installed."
        ) from exc

    try:
        dataset = xr.open_dataset(
            path,
            engine="cfgrib",
            backend_kwargs={
                "indexpath": "",
            },
        )
    except Exception as exc:
        raise EnvironmentalForcingError(
            "Unable to open ECMWF GRIB with cfgrib: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    try:
        longitude_name = _coord_name(
            dataset,
            ("longitude", "lon"),
        )
        latitude_name = _coord_name(
            dataset,
            ("latitude", "lat"),
        )

        dataset_longitude = (
            longitude % 360.0
        )

        point = dataset.sel(
            {
                longitude_name: (
                    dataset_longitude
                ),
                latitude_name: (
                    latitude
                ),
            },
            method="nearest",
        )

        u_name = next(
            (
                name
                for name in (
                    "u10",
                    "10u",
                )
                if name in point
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
                if name in point
            ),
            None,
        )

        if (
            u_name is None
            or v_name is None
        ):
            raise EnvironmentalForcingError(
                "ECMWF GRIB does not contain u10/v10."
            )

        u = _scalar(
            point[u_name]
        )
        v = _scalar(
            point[v_name]
        )

        valid_time = None

        for name in (
            "valid_time",
            "time",
        ):
            if name in point.coords:
                valid_time = _iso_utc(
                    point[name].values
                )
                break

        sampled = {
            "longitude": _scalar(
                point[longitude_name]
            ),
            "latitude": _scalar(
                point[latitude_name]
            ),
            "valid_time": valid_time,
        }

        return (
            u,
            v,
            sampled,
        )
    finally:
        dataset.close()


def fetch_wind_at_point(
    *,
    longitude: float,
    latitude: float,
    target_time: datetime,
    file_ttl_seconds: int = DEFAULT_ECMWF_FILE_TTL_SECONDS,
) -> dict:
    path, run_time, step_hours = (
        _download_ecmwf_wind(
            target_time=target_time,
            ttl_seconds=file_ttl_seconds,
        )
    )

    u, v, sampled = (
        _cfgrib_wind_point(
            path,
            longitude=longitude,
            latitude=latitude,
        )
    )

    return {
        "source": "ECMWF Open Data",
        "model": "IFS",
        "run_time": run_time.isoformat(),
        "forecast_step_hours": (
            step_hours
        ),
        "valid_time": sampled.get(
            "valid_time"
        ),
        "sampled_location": {
            "longitude": sampled[
                "longitude"
            ],
            "latitude": sampled[
                "latitude"
            ],
        },
        "u10_m_s": round(
            u,
            6,
        ),
        "v10_m_s": round(
            v,
            6,
        ),
        "speed_m_s": round(
            vector_speed(
                u,
                v,
            ),
            6,
        ),
        "direction_to_deg": (
            None
            if direction_to_deg(
                u,
                v,
            )
            is None
            else round(
                direction_to_deg(
                    u,
                    v,
                ),
                2,
            )
        ),
        "direction_from_deg": (
            None
            if direction_from_deg(
                u,
                v,
            )
            is None
            else round(
                direction_from_deg(
                    u,
                    v,
                ),
                2,
            )
        ),
        "grib_cache_path": str(
            path
        ),
    }


def _time_offset_minutes(
    valid_time: str | None,
    target_time: datetime,
) -> float | None:
    if not valid_time:
        return None

    text = valid_time

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(
            text
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )
    else:
        parsed = parsed.astimezone(
            timezone.utc
        )

    return round(
        (
            parsed - target_time
        ).total_seconds()
        / 60.0,
        1,
    )


def get_environmental_forcing(
    *,
    longitude: float,
    latitude: float,
    at: str | datetime | None = None,
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
) -> dict:
    validate_location(
        longitude,
        latitude,
    )

    target_time = normalize_target_time(
        at
    )

    cache_path = _combined_cache_path(
        longitude,
        latitude,
        target_time,
    )

    cached = _read_json_cache(
        cache_path,
        cache_ttl_seconds,
    )

    if cached is not None:
        cached["cache"] = {
            "status": "fresh",
            "path": str(
                cache_path
            ),
        }
        return cached

    current = fetch_current_at_point(
        longitude=longitude,
        latitude=latitude,
        target_time=target_time,
    )

    wave = fetch_wave_at_point(
        longitude=longitude,
        latitude=latitude,
        target_time=target_time,
    )

    wind = fetch_wind_at_point(
        longitude=longitude,
        latitude=latitude,
        target_time=target_time,
    )

    payload = {
        "target_time": target_time.isoformat(),
        "location": {
            "longitude": round(
                float(longitude),
                6,
            ),
            "latitude": round(
                float(latitude),
                6,
            ),
        },
        "current": current,
        "wave": wave,
        "wind": wind,
        "time_alignment_minutes": {
            "current": _time_offset_minutes(
                current.get(
                    "valid_time"
                ),
                target_time,
            ),
            "wave": _time_offset_minutes(
                wave.get(
                    "valid_time"
                ),
                target_time,
            ),
            "wind": _time_offset_minutes(
                wind.get(
                    "valid_time"
                ),
                target_time,
            ),
        },
        "openoil_ready_fields": {
            "x_sea_water_velocity": (
                current["u_m_s"]
            ),
            "y_sea_water_velocity": (
                current["v_m_s"]
            ),
            "x_wind": wind["u10_m_s"],
            "y_wind": wind["v10_m_s"],
            "sea_surface_wave_stokes_drift_x_velocity": (
                wave["stokes_u_m_s"]
            ),
            "sea_surface_wave_stokes_drift_y_velocity": (
                wave["stokes_v_m_s"]
            ),
            "sea_surface_wave_significant_height": (
                wave[
                    "significant_wave_height_m"
                ]
            ),
        },
        "generated_at": utc_now().isoformat(),
    }

    _write_json_cache(
        cache_path,
        payload,
    )

    payload["cache"] = {
        "status": "live",
        "path": str(
            cache_path
        ),
    }

    return payload
