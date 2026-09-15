from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATASET_ID = "cmems_mod_blk_phy-cur_anfc_2.5km_PT1H-m"

# Official dataset extent from Copernicus Marine catalogue.
MIN_LONGITUDE = 27.25
MAX_LONGITUDE = 42.0
MIN_LATITUDE = 40.5
MAX_LATITUDE = 47.32500076293945

# Shallowest model level reported by the current dataset metadata.
SURFACE_DEPTH_M = 0.5001727938652039

DEFAULT_STRIDE = 8
DEFAULT_CACHE_TTL_SECONDS = 30 * 60


class OceanCurrentsError(RuntimeError):
    pass


class OceanCurrentsInputError(ValueError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_target_time(value: str | datetime | None) -> datetime:
    if value is None:
        parsed = _utc_now()
    elif isinstance(value, datetime):
        parsed = value
    else:
        cleaned = value.strip()

        if not cleaned:
            parsed = _utc_now()
        else:
            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1] + "+00:00"

            try:
                parsed = datetime.fromisoformat(cleaned)
            except ValueError as exc:
                raise OceanCurrentsInputError(
                    "Invalid 'at' datetime. Use ISO 8601, "
                    "for example 2026-09-15T06:00:00Z."
                ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return parsed.replace(
        minute=0,
        second=0,
        microsecond=0,
    )


def direction_degrees(u: float, v: float) -> float:
    """
    Direction the water is moving TO, degrees clockwise from true north.

    u > 0 = eastward
    v > 0 = northward
    """
    return (math.degrees(math.atan2(u, v)) + 360.0) % 360.0


def _iso_datetime(value: Any) -> str:
    # xarray commonly exposes time coordinates as numpy.datetime64.
    # Calling .item() on nanosecond-resolution numpy.datetime64 may
    # produce a raw integer timestamp, so handle numpy datetime values
    # before generic scalar conversion.
    try:
        import numpy as np

        if isinstance(value, np.datetime64):
            if np.isnat(value):
                return str(value)

            text = np.datetime_as_string(
                value,
                unit="s",
                timezone="UTC",
            )

            if text.endswith("Z"):
                text = text[:-1] + "+00:00"

            return text
    except ImportError:
        pass

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value)

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return str(value)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.isoformat()


def build_currents_payload(
    dataset,
    *,
    target_time: datetime,
    stride: int = DEFAULT_STRIDE,
) -> dict:
    if stride < 1:
        raise OceanCurrentsInputError(
            "stride must be at least 1."
        )

    working = dataset

    if "time" in working.dims:
        if working.sizes.get("time", 0) < 1:
            raise OceanCurrentsError(
                "Copernicus returned no time steps."
            )
        working = working.isel(time=0)

    if "depth" in working.dims:
        if working.sizes.get("depth", 0) < 1:
            raise OceanCurrentsError(
                "Copernicus returned no depth levels."
            )
        working = working.isel(depth=0)

    for required in (
        "uo",
        "vo",
        "latitude",
        "longitude",
    ):
        if required not in working:
            if required not in working.coords:
                raise OceanCurrentsError(
                    f"Copernicus response is missing '{required}'."
                )

    latitudes = working["latitude"].values[::stride]
    longitudes = working["longitude"].values[::stride]

    u_values = working["uo"].values[
        ::stride,
        ::stride,
    ]
    v_values = working["vo"].values[
        ::stride,
        ::stride,
    ]

    vectors = []

    for lat_index, latitude in enumerate(latitudes):
        for lon_index, longitude in enumerate(longitudes):
            try:
                u = float(
                    u_values[
                        lat_index,
                        lon_index,
                    ]
                )
                v = float(
                    v_values[
                        lat_index,
                        lon_index,
                    ]
                )
            except (TypeError, ValueError):
                continue

            if not (
                math.isfinite(u)
                and math.isfinite(v)
            ):
                continue

            speed = math.hypot(u, v)

            vectors.append(
                {
                    "longitude": round(
                        float(longitude),
                        6,
                    ),
                    "latitude": round(
                        float(latitude),
                        6,
                    ),
                    "u": round(u, 6),
                    "v": round(v, 6),
                    "speed": round(speed, 6),
                    "direction_deg": round(
                        direction_degrees(u, v),
                        2,
                    ),
                }
            )

    if not vectors:
        raise OceanCurrentsError(
            "Copernicus returned no usable surface-current vectors."
        )

    valid_time = target_time.isoformat()

    if "time" in dataset.coords:
        time_values = dataset["time"].values

        if getattr(time_values, "size", 0):
            valid_time = _iso_datetime(
                time_values.flat[0]
            )

    depth_m = SURFACE_DEPTH_M

    if "depth" in dataset.coords:
        depth_values = dataset["depth"].values

        if getattr(depth_values, "size", 0):
            try:
                depth_m = float(
                    depth_values.flat[0]
                )
            except (TypeError, ValueError):
                pass

    return {
        "dataset_id": DATASET_ID,
        "source": "Copernicus Marine",
        "product": "BLKSEA_ANALYSISFORECAST_PHY_007_001",
        "variable_units": "m/s",
        "valid_time": valid_time,
        "requested_time": target_time.isoformat(),
        "depth_m": depth_m,
        "precision": "model_grid",
        "bbox": {
            "west": MIN_LONGITUDE,
            "south": MIN_LATITUDE,
            "east": MAX_LONGITUDE,
            "north": MAX_LATITUDE,
        },
        "grid": {
            "native_step_deg": 0.025,
            "stride": stride,
            "display_step_deg": round(
                0.025 * stride,
                6,
            ),
        },
        "vector_count": len(vectors),
        "vectors": vectors,
    }


def _cache_directory() -> Path:
    configured = os.getenv(
        "OCEAN_CURRENTS_CACHE_DIR"
    )

    if configured:
        return Path(configured)

    return (
        Path(tempfile.gettempdir())
        / "black-sea-eco-monitor"
        / "ocean-currents"
    )


def _cache_path(
    *,
    target_time: datetime,
    stride: int,
) -> Path:
    stamp = target_time.strftime("%Y%m%dT%H00Z")

    return (
        _cache_directory()
        / f"currents_{stamp}_s{stride}.json"
    )


def _read_cache(
    path: Path,
    *,
    ttl_seconds: int | None,
) -> dict | None:
    if not path.exists():
        return None

    if ttl_seconds is not None:
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
        # Cache failure must never make live ocean data unavailable.
        pass


def _open_remote_dataset(
    *,
    target_time: datetime,
):
    try:
        import copernicusmarine
    except ImportError as exc:
        raise OceanCurrentsError(
            "The 'copernicusmarine' package is not installed."
        ) from exc

    timestamp = target_time.isoformat()

    return copernicusmarine.open_dataset(
        dataset_id=DATASET_ID,
        variables=["uo", "vo"],
        minimum_longitude=MIN_LONGITUDE,
        maximum_longitude=MAX_LONGITUDE,
        minimum_latitude=MIN_LATITUDE,
        maximum_latitude=MAX_LATITUDE,
        start_datetime=timestamp,
        end_datetime=timestamp,
        minimum_depth=SURFACE_DEPTH_M,
        maximum_depth=SURFACE_DEPTH_M,
    )


def get_surface_currents(
    *,
    at: str | datetime | None = None,
    stride: int = DEFAULT_STRIDE,
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
) -> dict:
    if not (1 <= stride <= 40):
        raise OceanCurrentsInputError(
            "stride must be between 1 and 40."
        )

    target_time = normalize_target_time(at)

    cache_path = _cache_path(
        target_time=target_time,
        stride=stride,
    )

    cached = _read_cache(
        cache_path,
        ttl_seconds=cache_ttl_seconds,
    )

    if cached is not None:
        cached["cache"] = {
            "status": "fresh",
            "path": str(cache_path),
        }
        return cached

    dataset = None

    try:
        dataset = _open_remote_dataset(
            target_time=target_time,
        )

        payload = build_currents_payload(
            dataset,
            target_time=target_time,
            stride=stride,
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
            "path": str(cache_path),
        }

        return payload

    except OceanCurrentsInputError:
        raise
    except Exception as exc:
        stale = _read_cache(
            cache_path,
            ttl_seconds=None,
        )

        if stale is not None:
            stale["cache"] = {
                "status": "stale_fallback",
                "path": str(cache_path),
                "live_error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            }
            return stale

        if isinstance(
            exc,
            OceanCurrentsError,
        ):
            raise

        raise OceanCurrentsError(
            "Unable to fetch Black Sea current data "
            f"from Copernicus Marine: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    finally:
        if (
            dataset is not None
            and hasattr(dataset, "close")
        ):
            dataset.close()
