from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
import json

import numpy as np
import rasterio

from backend.services.sentinel5p_provider import (
    DEFAULT_BLACK_SEA_BBOX,
    Sentinel5PProvider,
    product_info,
    satellite_semantics,
)


DEFAULT_MAX_LOOKBACK_DAYS = 7


class Sentinel5PNoCoverageError(RuntimeError):
    """No valid TROPOMI pixels were found in the requested lookback window."""


def _finite_stats(values: np.ndarray) -> dict[str, Any]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "p05": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p95": None,
        }

    finite64 = finite.astype(np.float64, copy=False)
    p05, p25, p50, p75, p95 = np.percentile(
        finite64,
        [5, 25, 50, 75, 95],
    )
    return {
        "count": int(finite64.size),
        "min": float(np.min(finite64)),
        "max": float(np.max(finite64)),
        "mean": float(np.mean(finite64)),
        "p05": float(p05),
        "p25": float(p25),
        "p50": float(p50),
        "p75": float(p75),
        "p95": float(p95),
    }


def _day_window(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return start, end


def _load_sidecar(metadata_path: Path | None) -> dict[str, Any]:
    if metadata_path is None or not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def read_satellite_field(
    *,
    geotiff_path: str | Path,
    metadata_path: str | Path | None = None,
    product: str = "no2",
    stride: int = 1,
    cache_hit: bool | None = None,
) -> dict[str, Any]:
    if not 1 <= int(stride) <= 8:
        raise ValueError("stride must be between 1 and 8.")

    geotiff = Path(geotiff_path)
    sidecar = Path(metadata_path) if metadata_path is not None else None
    metadata = _load_sidecar(sidecar)
    info = product_info(product)
    product_key = product.strip().lower()

    with rasterio.open(geotiff) as ds:
        if ds.count < 2:
            raise ValueError(
                "Sentinel-5P GeoTIFF must contain value band + dataMask band."
            )
        if ds.crs is None or str(ds.crs).upper() != "EPSG:4326":
            raise ValueError(
                f"Expected EPSG:4326 Sentinel-5P GeoTIFF, got {ds.crs!s}."
            )

        values_raw = ds.read(1).astype(np.float64, copy=False)
        mask_raw = ds.read(2).astype(np.float64, copy=False)

        valid_raw = (
            np.isfinite(values_raw)
            & np.isfinite(mask_raw)
            & (mask_raw > 0)
        )

        source_height = int(ds.height)
        source_width = int(ds.width)
        total_count = source_height * source_width
        valid_count = int(np.count_nonzero(valid_raw))
        source_stats = _finite_stats(values_raw[valid_raw])

        # GeoTIFF rows are north -> south.
        # Canonical API latitude is ascending south -> north.
        values_asc = np.flipud(values_raw)
        valid_asc = np.flipud(valid_raw)

        transform = ds.transform
        longitude_full = np.array(
            [
                transform.c + (col + 0.5) * transform.a
                for col in range(source_width)
            ],
            dtype=np.float64,
        )
        latitude_desc = np.array(
            [
                transform.f + (row + 0.5) * transform.e
                for row in range(source_height)
            ],
            dtype=np.float64,
        )
        latitude_full = latitude_desc[::-1]

        row_idx = np.arange(0, source_height, int(stride))
        col_idx = np.arange(0, source_width, int(stride))

        longitude = longitude_full[col_idx]
        latitude = latitude_full[row_idx]
        sampled_values = values_asc[np.ix_(row_idx, col_idx)]
        sampled_valid = valid_asc[np.ix_(row_idx, col_idx)]

        values_json: list[list[float | None]] = []
        for row_values, row_valid in zip(sampled_values, sampled_valid):
            row: list[float | None] = []
            for value, is_valid in zip(row_values, row_valid):
                row.append(float(value) if bool(is_valid) else None)
            values_json.append(row)

        returned_stats = _finite_stats(sampled_values[sampled_valid])

        bounds = {
            "west": float(ds.bounds.left),
            "south": float(ds.bounds.bottom),
            "east": float(ds.bounds.right),
            "north": float(ds.bounds.top),
        }
        resolution_lon = abs(float(transform.a))
        resolution_lat = abs(float(transform.e))

    semantics = metadata.get(
        "semantics",
        satellite_semantics(product_key),
    )

    return {
        "provider": metadata.get(
            "provider",
            "Copernicus Data Space Ecosystem / Sentinel Hub",
        ),
        "collection": metadata.get("collection", "sentinel-5p-l2"),
        "platform": metadata.get("platform", "Sentinel-5P"),
        "instrument": metadata.get("instrument", "TROPOMI"),
        "product": product_key,
        "band": metadata.get("band", info["band"]),
        "quantity": metadata.get("quantity", info["quantity"]),
        "units": metadata.get("units", info["units"]),
        "semantics": semantics,
        "time_from": metadata.get("time_from"),
        "time_to": metadata.get("time_to"),
        "timeliness": metadata.get("timeliness"),
        "min_qa": metadata.get("min_qa"),
        "bbox": bounds,
        "grid": {
            "crs": "EPSG:4326",
            "source_width": source_width,
            "source_height": source_height,
            "width": int(len(longitude)),
            "height": int(len(latitude)),
            "stride": int(stride),
            "source_resolution_degrees": {
                "longitude": resolution_lon,
                "latitude": resolution_lat,
            },
            "coordinate_semantics": "pixel_centres",
            "latitude_order": "ascending",
            "longitude_order": "ascending",
            "resampling": metadata.get("upsampling", "NEAREST"),
        },
        "longitude": [float(x) for x in longitude],
        "latitude": [float(y) for y in latitude],
        "values": values_json,
        "statistics": source_stats,
        "returned_grid_statistics": returned_stats,
        "coverage": {
            "valid_pixel_count": valid_count,
            "total_pixel_count": total_count,
            "valid_fraction": (
                float(valid_count / total_count) if total_count else 0.0
            ),
            "valid_percent": (
                float(100.0 * valid_count / total_count)
                if total_count
                else 0.0
            ),
            "invalid_policy": "dataMask<=0 or non-finite value -> null",
        },
        "provenance": {
            "cache_hit": cache_hit,
            "geotiff": str(geotiff),
            "metadata": str(sidecar) if sidecar is not None else None,
            "sha256": metadata.get("sha256"),
            "fetched_at": metadata.get("fetched_at"),
            "sample_type": metadata.get("sample_type", "FLOAT32"),
            "source_bands": metadata.get(
                "bands",
                [info["band"], "dataMask"],
            ),
        },
    }


def fetch_satellite_field_for_day(
    *,
    product: str,
    day: date,
    timeliness: str,
    stride: int,
    provider: Sentinel5PProvider,
) -> dict[str, Any]:
    start, end = _day_window(day)

    artifact = provider.fetch_geotiff(
        product=product,
        start=start,
        end=end,
        bbox=DEFAULT_BLACK_SEA_BBOX,
        width=350,
        height=180,
        timeliness=timeliness,
    )

    field = read_satellite_field(
        geotiff_path=artifact.path,
        metadata_path=artifact.metadata_path,
        product=product,
        stride=stride,
        cache_hit=artifact.cache_hit,
    )
    field["selection"] = {
        "mode": "exact_date",
        "requested_date": day.isoformat(),
        "resolved_date": day.isoformat(),
        "lookback_days": 0,
        "candidates_checked": [day.isoformat()],
    }
    return field


def fetch_latest_available_satellite_field(
    *,
    product: str = "no2",
    timeliness: str = "NRTI",
    stride: int = 1,
    max_lookback_days: int = DEFAULT_MAX_LOOKBACK_DAYS,
    provider: Sentinel5PProvider | None = None,
    reference_day: date | None = None,
) -> dict[str, Any]:
    if not 0 <= int(max_lookback_days) <= 14:
        raise ValueError("max_lookback_days must be between 0 and 14.")

    provider = provider or Sentinel5PProvider()
    reference_day = reference_day or datetime.now(timezone.utc).date()

    checked: list[str] = []

    for offset in range(int(max_lookback_days) + 1):
        candidate = reference_day - timedelta(days=offset)
        checked.append(candidate.isoformat())

        field = fetch_satellite_field_for_day(
            product=product,
            day=candidate,
            timeliness=timeliness,
            stride=stride,
            provider=provider,
        )

        if field["coverage"]["valid_pixel_count"] > 0:
            field["selection"] = {
                "mode": "latest_available",
                "requested_date": None,
                "reference_date": reference_day.isoformat(),
                "resolved_date": candidate.isoformat(),
                "lookback_days": offset,
                "max_lookback_days": int(max_lookback_days),
                "candidates_checked": checked,
            }
            return field

    raise Sentinel5PNoCoverageError(
        "No valid Sentinel-5P/TROPOMI pixels found for "
        f"{product} within {int(max_lookback_days)} day(s) before "
        f"{reference_day.isoformat()}."
    )


def fetch_satellite_field(
    *,
    product: str = "no2",
    day: date | None = None,
    timeliness: str = "NRTI",
    stride: int = 1,
    max_lookback_days: int = DEFAULT_MAX_LOOKBACK_DAYS,
    provider: Sentinel5PProvider | None = None,
) -> dict[str, Any]:
    provider = provider or Sentinel5PProvider()

    if day is not None:
        return fetch_satellite_field_for_day(
            product=product,
            day=day,
            timeliness=timeliness,
            stride=stride,
            provider=provider,
        )

    return fetch_latest_available_satellite_field(
        product=product,
        timeliness=timeliness,
        stride=stride,
        max_lookback_days=max_lookback_days,
        provider=provider,
    )
