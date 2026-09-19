from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agents.ocean_data.copernicus_currents import (
    DATASET_ID,
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    SURFACE_DEPTH_M,
    normalize_target_time,
)


STANDARD_HORIZONS_HOURS = (6, 12, 24, 48, 72)

DEFAULT_HOURS = 72
DEFAULT_PARTICLES = 500
DEFAULT_RADIUS_M = 500.0
DEFAULT_DIFFUSIVITY_M2_S = 2.0
DEFAULT_TIME_STEP_SECONDS = 900
DEFAULT_OUTPUT_STEP_SECONDS = 3600
DEFAULT_CACHE_TTL_SECONDS = 15 * 60
FORCING_MARGIN_DEG = 4.0

# WEATHER1_3B_CURRENTS_PLUS_WIND
FORCING_MODE_CURRENT_ONLY = "current_only"
FORCING_MODE_CURRENTS_PLUS_WIND = "currents_plus_wind"
SUPPORTED_FORCING_MODES = (
    FORCING_MODE_CURRENT_ONLY,
    FORCING_MODE_CURRENTS_PLUS_WIND,
)
DEFAULT_FORCING_MODE = FORCING_MODE_CURRENT_ONLY
DEFAULT_WIND_DRIFT_FACTOR = 0.02

MIN_PARTICLES = 50
MAX_PARTICLES = 2000
MAX_RADIUS_M = 20_000.0
MAX_DIFFUSIVITY_M2_S = 100.0


class OceanDriftError(RuntimeError):
    pass


class OceanDriftInputError(ValueError):
    pass


def normalize_forcing_mode(
    value: str | None,
) -> str:
    mode = str(value or DEFAULT_FORCING_MODE).strip().lower()

    if mode not in SUPPORTED_FORCING_MODES:
        raise OceanDriftInputError(
            "forcing_mode must be one of: "
            + ", ".join(SUPPORTED_FORCING_MODES)
            + "."
        )

    return mode


def drift_scope(
    forcing_mode: str,
) -> str:
    mode = normalize_forcing_mode(forcing_mode)

    if mode == FORCING_MODE_CURRENTS_PLUS_WIND:
        return (
            "passive_surface_tracer_currents_plus_direct_windage"
        )

    return "passive_surface_tracer_current_only"


def wind_drift_factor_for_mode(
    forcing_mode: str,
) -> float:
    mode = normalize_forcing_mode(forcing_mode)

    if mode == FORCING_MODE_CURRENTS_PLUS_WIND:
        return DEFAULT_WIND_DRIFT_FACTOR

    return 0.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(value: Any) -> str:
    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value)

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return str(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return parsed.isoformat()


def validate_drift_request(
    *,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
) -> None:
    if not (
        MIN_LONGITUDE
        <= longitude
        <= MAX_LONGITUDE
    ):
        raise OceanDriftInputError(
            "longitude must be inside the Copernicus Black Sea domain "
            f"({MIN_LONGITUDE}..{MAX_LONGITUDE})."
        )

    if not (
        MIN_LATITUDE
        <= latitude
        <= MAX_LATITUDE
    ):
        raise OceanDriftInputError(
            "latitude must be inside the Copernicus Black Sea domain "
            f"({MIN_LATITUDE}..{MAX_LATITUDE})."
        )

    if hours not in STANDARD_HORIZONS_HOURS:
        raise OceanDriftInputError(
            "hours must be one of: "
            + ", ".join(
                str(value)
                for value in STANDARD_HORIZONS_HOURS
            )
            + "."
        )

    if not (
        MIN_PARTICLES
        <= particles
        <= MAX_PARTICLES
    ):
        raise OceanDriftInputError(
            f"particles must be between {MIN_PARTICLES} "
            f"and {MAX_PARTICLES}."
        )

    if not (
        0
        <= radius_m
        <= MAX_RADIUS_M
    ):
        raise OceanDriftInputError(
            f"radius_m must be between 0 and {MAX_RADIUS_M:g}."
        )

    if not (
        0
        <= diffusivity_m2_s
        <= MAX_DIFFUSIVITY_M2_S
    ):
        raise OceanDriftInputError(
            "diffusivity_m2_s must be between 0 and "
            f"{MAX_DIFFUSIVITY_M2_S:g}."
        )


def requested_horizons(
    hours: int,
) -> tuple[int, ...]:
    if hours not in STANDARD_HORIZONS_HOURS:
        raise OceanDriftInputError(
            "Unsupported forecast horizon."
        )

    return tuple(
        value
        for value in STANDARD_HORIZONS_HOURS
        if value <= hours
    )


def forcing_bbox(
    *,
    longitude: float,
    latitude: float,
    margin_deg: float = FORCING_MARGIN_DEG,
) -> dict[str, float]:
    return {
        "west": max(
            MIN_LONGITUDE,
            longitude - margin_deg,
        ),
        "south": max(
            MIN_LATITUDE,
            latitude - margin_deg,
        ),
        "east": min(
            MAX_LONGITUDE,
            longitude + margin_deg,
        ),
        "north": min(
            MAX_LATITUDE,
            latitude + margin_deg,
        ),
    }


def _cache_directory() -> Path:
    configured = os.getenv(
        "OCEAN_DRIFT_CACHE_DIR"
    )

    if configured:
        return Path(configured)

    return (
        Path(tempfile.gettempdir())
        / "black-sea-eco-monitor"
        / "ocean-drift"
    )


def _cache_key(
    *,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
    forcing_mode: str = DEFAULT_FORCING_MODE,
) -> str:
    canonical = json.dumps(
        {
            "start_time": start_time.isoformat(),
            "longitude": round(longitude, 6),
            "latitude": round(latitude, 6),
            "hours": hours,
            "particles": particles,
            "radius_m": round(radius_m, 3),
            "diffusivity_m2_s": round(
                diffusivity_m2_s,
                3,
            ),
            "forcing_mode": normalize_forcing_mode(
                forcing_mode
            ),
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:20]


def _cache_path(**kwargs) -> Path:
    return (
        _cache_directory()
        / (
            "drift_"
            + _cache_key(**kwargs)
            + ".json"
        )
    )


def _read_cache(
    path: Path,
    *,
    ttl_seconds: int,
) -> dict | None:
    if not path.exists():
        return None

    age_seconds = (
        _utc_now().timestamp()
        - path.stat().st_mtime
    )

    if age_seconds > ttl_seconds:
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


def _write_cache(
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
        # Drift simulation must not fail only because cache is unavailable.
        pass


def _open_forcing_dataset(
    *,
    start_time: datetime,
    hours: int,
    longitude: float,
    latitude: float,
):
    try:
        import copernicusmarine
    except ImportError as exc:
        raise OceanDriftError(
            "The 'copernicusmarine' package is not installed."
        ) from exc

    bbox = forcing_bbox(
        longitude=longitude,
        latitude=latitude,
    )

    # One extra model hour gives OpenDrift interpolation room
    # at the requested simulation endpoint.
    end_time = (
        start_time
        + timedelta(hours=hours + 1)
    )

    return copernicusmarine.open_dataset(
        dataset_id=DATASET_ID,
        variables=["uo", "vo"],
        minimum_longitude=bbox["west"],
        maximum_longitude=bbox["east"],
        minimum_latitude=bbox["south"],
        maximum_latitude=bbox["north"],
        start_datetime=start_time.isoformat(),
        end_datetime=end_time.isoformat(),
        minimum_depth=SURFACE_DEPTH_M,
        maximum_depth=SURFACE_DEPTH_M,
    )


def _build_opendrift_reader(
    dataset,
):
    try:
        from opendrift.readers import (
            reader_netCDF_CF_generic,
        )
    except ImportError as exc:
        raise OceanDriftError(
            "OpenDrift is not installed."
        ) from exc

    # The Copernicus Black Sea dataset exposes uo/vo.
    # Explicit mapping keeps the integration independent
    # of optional CF metadata details.
    return reader_netCDF_CF_generic.Reader(
        dataset,
        name="Copernicus Black Sea surface currents",
        standard_name_mapping={
            "uo": "x_sea_water_velocity",
            "vo": "y_sea_water_velocity",
        },
    )


def _run_opendrift(
    *,
    dataset,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
    wind_reader=None,
    wind_drift_factor: float = 0.0,
):
    try:
        from opendrift.models.oceandrift import (
            OceanDrift,
        )
    except ImportError as exc:
        raise OceanDriftError(
            "OpenDrift is not installed."
        ) from exc

    reader = _build_opendrift_reader(
        dataset
    )

    model = OceanDrift(
        loglevel=30,
        seed=0,
    )

    model.add_reader(reader)

    if wind_reader is not None:
        model.add_reader(wind_reader)

    # Surface tracer: currents are always enabled.
    # WEATHER-1.3B optionally adds direct windage through OpenDrift.
    model.set_config(
        "drift:vertical_mixing",
        False,
    )
    model.set_config(
        "drift:vertical_advection",
        False,
    )
    model.set_config(
        "drift:stokes_drift",
        False,
    )
    model.set_config(
        "environment:constant:horizontal_diffusivity",
        float(diffusivity_m2_s),
    )
    model.set_config(
        "general:coastline_action",
        "previous",
    )

    model.seed_elements(
        lon=float(longitude),
        lat=float(latitude),
        radius=float(radius_m),
        number=int(particles),
        time=start_time.replace(
            tzinfo=None
        ),
        z=0,
        wind_drift_factor=float(wind_drift_factor),
        current_drift_factor=1.0,
    )

    result = model.run(
        duration=timedelta(
            hours=hours
        ),
        time_step=DEFAULT_TIME_STEP_SECONDS,
        time_step_output=DEFAULT_OUTPUT_STEP_SECONDS,
    )

    return result


def _finite_points(
    longitudes,
    latitudes,
    statuses=None,
) -> list[list[float]]:
    points: list[list[float]] = []

    count = min(
        len(longitudes),
        len(latitudes),
    )

    for index in range(count):
        try:
            longitude = float(
                longitudes[index]
            )
            latitude = float(
                latitudes[index]
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if not (
            math.isfinite(longitude)
            and math.isfinite(latitude)
        ):
            continue

        if statuses is not None:
            try:
                status = float(
                    statuses[index]
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if not math.isfinite(status):
                continue

            # OpenDrift result points with status < 0
            # are not valid particle positions.
            if status < 0:
                continue

        points.append(
            [
                round(longitude, 6),
                round(latitude, 6),
            ]
        )

    return points


def _convex_hull(
    points: list[list[float]],
) -> list[list[float]] | None:
    unique = sorted(
        {
            (
                float(point[0]),
                float(point[1]),
            )
            for point in points
        }
    )

    if len(unique) < 3:
        return None

    def cross(origin, a, b):
        return (
            (a[0] - origin[0])
            * (b[1] - origin[1])
            - (a[1] - origin[1])
            * (b[0] - origin[0])
        )

    lower = []

    for point in unique:
        while (
            len(lower) >= 2
            and cross(
                lower[-2],
                lower[-1],
                point,
            )
            <= 0
        ):
            lower.pop()

        lower.append(point)

    upper = []

    for point in reversed(unique):
        while (
            len(upper) >= 2
            and cross(
                upper[-2],
                upper[-1],
                point,
            )
            <= 0
        ):
            upper.pop()

        upper.append(point)

    hull = (
        lower[:-1]
        + upper[:-1]
    )

    ring = [
        [
            round(point[0], 6),
            round(point[1], 6),
        ]
        for point in hull
    ]

    ring.append(ring[0])

    return ring


def summarize_points(
    points: list[list[float]],
) -> dict:
    if not points:
        return {
            "particle_count": 0,
            "center": None,
            "bbox": None,
            "envelope": None,
        }

    longitudes = [
        point[0]
        for point in points
    ]
    latitudes = [
        point[1]
        for point in points
    ]

    center = {
        "longitude": round(
            sum(longitudes)
            / len(longitudes),
            6,
        ),
        "latitude": round(
            sum(latitudes)
            / len(latitudes),
            6,
        ),
    }

    bbox = {
        "west": round(
            min(longitudes),
            6,
        ),
        "south": round(
            min(latitudes),
            6,
        ),
        "east": round(
            max(longitudes),
            6,
        ),
        "north": round(
            max(latitudes),
            6,
        ),
    }

    hull = _convex_hull(points)

    envelope = None

    if hull is not None:
        envelope = {
            "type": "Polygon",
            "coordinates": [hull],
        }

    return {
        "particle_count": len(points),
        "center": center,
        "bbox": bbox,
        "envelope": envelope,
    }


def _nearest_time_index(
    result,
    target_time: datetime,
) -> int:
    try:
        import numpy as np
    except ImportError as exc:
        raise OceanDriftError(
            "NumPy is required for drift result analysis."
        ) from exc

    raw_times = result["time"].values

    if len(raw_times) < 1:
        raise OceanDriftError(
            "OpenDrift returned no output times."
        )

    target = np.datetime64(
        target_time.replace(
            tzinfo=None
        )
    )

    differences = np.abs(
        raw_times - target
    )

    return int(
        differences.argmin()
    )


def _snapshot(
    result,
    *,
    start_time: datetime,
    horizon_hours: int,
) -> dict:
    target_time = (
        start_time
        + timedelta(
            hours=horizon_hours
        )
    )

    index = _nearest_time_index(
        result,
        target_time,
    )

    longitudes = (
        result["lon"]
        .isel(time=index)
        .values
    )
    latitudes = (
        result["lat"]
        .isel(time=index)
        .values
    )

    statuses = None

    if "status" in result:
        statuses = (
            result["status"]
            .isel(time=index)
            .values
        )

    points = _finite_points(
        longitudes,
        latitudes,
        statuses,
    )

    summary = summarize_points(
        points
    )

    valid_time = _iso_utc(
        result["time"]
        .isel(time=index)
        .values
    )

    return {
        "hours": horizon_hours,
        "time": valid_time,
        **summary,
        "points": points,
    }


def _mean_track(
    result,
) -> list[dict]:
    track = []

    time_count = int(
        result.sizes.get(
            "time",
            0,
        )
    )

    for index in range(
        time_count
    ):
        longitudes = (
            result["lon"]
            .isel(time=index)
            .values
        )
        latitudes = (
            result["lat"]
            .isel(time=index)
            .values
        )

        statuses = None

        if "status" in result:
            statuses = (
                result["status"]
                .isel(time=index)
                .values
            )

        points = _finite_points(
            longitudes,
            latitudes,
            statuses,
        )

        summary = summarize_points(
            points
        )

        if summary["center"] is None:
            continue

        track.append(
            {
                "time": _iso_utc(
                    result["time"]
                    .isel(time=index)
                    .values
                ),
                "longitude": (
                    summary["center"][
                        "longitude"
                    ]
                ),
                "latitude": (
                    summary["center"][
                        "latitude"
                    ]
                ),
                "particle_count": (
                    summary[
                        "particle_count"
                    ]
                ),
            }
        )

    return track


def build_drift_payload(
    result,
    *,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
    opendrift_version: str | None = None,
    forcing_mode: str = DEFAULT_FORCING_MODE,
    wind_forcing_provenance: dict | None = None,
) -> dict:
    forcing_mode = normalize_forcing_mode(
        forcing_mode
    )
    wind_factor = wind_drift_factor_for_mode(
        forcing_mode
    )

    not_included = [
        "wave / Stokes drift",
        "oil weathering",
        "evaporation",
        "emulsification",
        "oil viscosity changes",
    ]

    if forcing_mode == FORCING_MODE_CURRENT_ONLY:
        not_included.insert(0, "wind forcing")

    snapshots = [
        _snapshot(
            result,
            start_time=start_time,
            horizon_hours=horizon,
        )
        for horizon in requested_horizons(
            hours
        )
    ]

    return {
        "model": "OpenDrift OceanDrift",
        "model_version": opendrift_version,
        "scope": drift_scope(forcing_mode),
        "forcing_mode": forcing_mode,
        "forcing": {
            "source": "Copernicus Marine",
            "dataset_id": DATASET_ID,
            "variables": ["uo", "vo"],
            "depth_m": SURFACE_DEPTH_M,
            "bbox": forcing_bbox(
                longitude=longitude,
                latitude=latitude,
            ),
            "wind": (
                wind_forcing_provenance
                if forcing_mode
                == FORCING_MODE_CURRENTS_PLUS_WIND
                else {
                    "enabled": False,
                    "reason": "current_only forcing mode",
                }
            ),
        },
        "seed": {
            "longitude": round(
                float(longitude),
                6,
            ),
            "latitude": round(
                float(latitude),
                6,
            ),
            "particle_count": int(
                particles
            ),
            "radius_m": float(
                radius_m
            ),
            "radius_semantics": (
                "OpenDrift Gaussian seeding radius "
                "(approximately one standard deviation)"
            ),
        },
        "simulation": {
            "start_time": start_time.isoformat(),
            "forecast_hours": int(
                hours
            ),
            "integration_step_seconds": (
                DEFAULT_TIME_STEP_SECONDS
            ),
            "output_step_seconds": (
                DEFAULT_OUTPUT_STEP_SECONDS
            ),
            "horizontal_diffusivity_m2_s": float(
                diffusivity_m2_s
            ),
            "wind_drift_factor": float(
                wind_factor
            ),
            "current_drift_factor": 1.0,
            "coastline_action": "previous",
        },
        "not_included": not_included,
        "horizons": snapshots,
        "mean_track": _mean_track(
            result
        ),
    }


def run_surface_drift(
    *,
    longitude: float,
    latitude: float,
    at: str | datetime | None = None,
    hours: int = DEFAULT_HOURS,
    particles: int = DEFAULT_PARTICLES,
    radius_m: float = DEFAULT_RADIUS_M,
    diffusivity_m2_s: float = DEFAULT_DIFFUSIVITY_M2_S,
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    forcing_mode: str = DEFAULT_FORCING_MODE,
) -> dict:
    validate_drift_request(
        longitude=longitude,
        latitude=latitude,
        hours=hours,
        particles=particles,
        radius_m=radius_m,
        diffusivity_m2_s=diffusivity_m2_s,
    )

    forcing_mode = normalize_forcing_mode(
        forcing_mode
    )

    start_time = normalize_target_time(
        at
    )

    cache_path = _cache_path(
        start_time=start_time,
        longitude=longitude,
        latitude=latitude,
        hours=hours,
        particles=particles,
        radius_m=radius_m,
        diffusivity_m2_s=diffusivity_m2_s,
        forcing_mode=forcing_mode,
    )

    cached = _read_cache(
        cache_path,
        ttl_seconds=cache_ttl_seconds,
    )

    if cached is not None:
        cached["cache"] = {
            "status": "fresh",
            "path": str(
                cache_path
            ),
        }
        return cached

    dataset = None
    wind_forcing = None
    wind_reader = None
    wind_forcing_provenance = None

    try:
        dataset = _open_forcing_dataset(
            start_time=start_time,
            hours=hours,
            longitude=longitude,
            latitude=latitude,
        )

        if (
            forcing_mode
            == FORCING_MODE_CURRENTS_PLUS_WIND
        ):
            try:
                from backend.services.ecmwf_wind_forcing import (
                    EcmwfWindForcingBuilder,
                    build_opendrift_wind_reader,
                )
            except ImportError as exc:
                raise OceanDriftError(
                    "WEATHER-1.3A wind forcing module "
                    "is not available."
                ) from exc

            wind_forcing = (
                EcmwfWindForcingBuilder().build(
                    start_time=start_time,
                    hours=hours,
                    bbox=forcing_bbox(
                        longitude=longitude,
                        latitude=latitude,
                    ),
                )
            )
            wind_reader = build_opendrift_wind_reader(
                wind_forcing
            )
            wind_forcing_provenance = (
                wind_forcing.provenance()
            )

        result = _run_opendrift(
            dataset=dataset,
            start_time=start_time,
            longitude=longitude,
            latitude=latitude,
            hours=hours,
            particles=particles,
            radius_m=radius_m,
            diffusivity_m2_s=diffusivity_m2_s,
            wind_reader=wind_reader,
            wind_drift_factor=(
                wind_drift_factor_for_mode(
                    forcing_mode
                )
            ),
        )

        try:
            import opendrift

            version = getattr(
                opendrift,
                "__version__",
                None,
            )
        except ImportError:
            version = None

        payload = build_drift_payload(
            result,
            start_time=start_time,
            longitude=longitude,
            latitude=latitude,
            hours=hours,
            particles=particles,
            radius_m=radius_m,
            diffusivity_m2_s=diffusivity_m2_s,
            opendrift_version=version,
            forcing_mode=forcing_mode,
            wind_forcing_provenance=(
                wind_forcing_provenance
            ),
        )

        payload["generated_at"] = (
            _utc_now().isoformat()
        )

        _write_cache(
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

    except OceanDriftInputError:
        raise
    except Exception as exc:
        if isinstance(
            exc,
            OceanDriftError,
        ):
            raise

        raise OceanDriftError(
            "Unable to calculate Black Sea drift forecast: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    finally:
        if (
            wind_forcing is not None
            and hasattr(
                wind_forcing.dataset,
                "close",
            )
        ):
            wind_forcing.dataset.close()

        if (
            dataset is not None
            and hasattr(
                dataset,
                "close",
            )
        ):
            dataset.close()
