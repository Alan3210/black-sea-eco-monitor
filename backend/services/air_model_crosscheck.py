from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import math
import re
import unicodedata

import numpy as np

from backend.services.cams_air_field import CamsAirFieldService
from backend.services.geos_cf_field import fetch_geos_cf_field


SUPPORTED_PRODUCTS = {"pm25", "pm10"}


class AirModelCrosscheckError(RuntimeError):
    pass


class AirModelCrosscheckUnavailable(AirModelCrosscheckError):
    pass


def _parse_utc(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    result = datetime.fromisoformat(text)
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def _utc_iso(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def nearest_cams_target(valid_time: str | datetime) -> dict[str, Any]:
    geos_time = (
        _parse_utc(valid_time)
        if isinstance(valid_time, str)
        else valid_time.astimezone(timezone.utc)
    )

    hour_fraction = (
        geos_time.hour
        + geos_time.minute / 60.0
        + geos_time.second / 3600.0
    )
    nearest_hour = int(math.floor(hour_fraction + 0.5))

    target_day = geos_time.date()
    if nearest_hour >= 24:
        target_day = target_day + timedelta(days=1)
        nearest_hour = 0

    target_time = datetime.combine(
        target_day,
        datetime.min.time(),
        tzinfo=timezone.utc,
    ) + timedelta(hours=nearest_hour)

    delta_minutes = abs(
        (target_time - geos_time).total_seconds()
    ) / 60.0

    return {
        "run_date": target_day,
        "lead_hour": nearest_hour,
        "target_valid_time": target_time,
        "delta_minutes_to_geos": delta_minutes,
    }


def _normalize_unit_text(value: Any) -> str:
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    text = text.replace("μ", "µ")
    text = text.replace("³", "3")
    text = text.replace("^3", "3")
    text = text.replace("m−3", "m-3")
    text = text.replace("m⁻3", "m-3")
    text = text.replace("m⁻³", "m-3")
    text = re.sub(r"\s+", "", text)

    aliases = {
        "µg/m3": "ug/m3",
        "ug/m3": "ug/m3",
        "µgm-3": "ug/m3",
        "ugm-3": "ug/m3",
        "µg/m-3": "ug/m3",
        "ug/m-3": "ug/m3",
    }
    return aliases.get(text, text)


def _extract_units(field: dict[str, Any]) -> str:
    for key in ("units", "unit"):
        value = field.get(key)
        if value not in (None, ""):
            return str(value)

    pollutant = field.get("pollutant")
    if isinstance(pollutant, dict):
        for key in ("units", "unit"):
            value = pollutant.get(key)
            if value not in (None, ""):
                return str(value)

    semantics = field.get("semantics")
    if isinstance(semantics, dict):
        value = semantics.get("units")
        if value not in (None, ""):
            return str(value)

    return ""


def _extract_source_variable(field: dict[str, Any]) -> str | None:
    value = field.get("source_variable")
    if value:
        return str(value)

    pollutant = field.get("pollutant")
    if isinstance(pollutant, dict):
        value = pollutant.get("source_variable")
        if value:
            return str(value)

    return None


def _first_present(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def _extract_grid_payload(
    field: dict[str, Any],
) -> tuple[list[Any], list[Any], list[Any]]:
    longitude = _first_present(
        field,
        ("longitude", "longitudes"),
    )
    latitude = _first_present(
        field,
        ("latitude", "latitudes"),
    )
    values = field.get("values")

    grid = field.get("grid")
    if isinstance(grid, dict):
        if longitude is None:
            longitude = _first_present(
                grid,
                ("longitude", "longitudes"),
            )
        if latitude is None:
            latitude = _first_present(
                grid,
                ("latitude", "latitudes"),
            )
        if values is None:
            values = grid.get("values")

    return (
        list(longitude) if longitude is not None else [],
        list(latitude) if latitude is not None else [],
        list(values) if values is not None else [],
    )


def _field_arrays(
    field: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    longitude_raw, latitude_raw, raw_values = _extract_grid_payload(field)

    longitude = np.asarray(longitude_raw, dtype=np.float64)
    latitude = np.asarray(latitude_raw, dtype=np.float64)

    values = np.empty(
        (len(latitude), len(longitude)),
        dtype=np.float64,
    )
    values.fill(np.nan)

    if len(raw_values) != len(latitude):
        raise AirModelCrosscheckError(
            "Canonical field row count does not match latitude."
        )

    for row_index, row in enumerate(raw_values):
        if len(row) != len(longitude):
            raise AirModelCrosscheckError(
                "Canonical field column count does not match longitude."
            )
        for col_index, value in enumerate(row):
            if value is None:
                continue
            number = float(value)
            if math.isfinite(number):
                values[row_index, col_index] = number

    if longitude.size < 2 or latitude.size < 2:
        raise AirModelCrosscheckError(
            "Cross-check requires at least a 2x2 rectilinear field."
        )

    if np.any(np.diff(longitude) <= 0):
        raise AirModelCrosscheckError(
            "Longitude coordinates must be strictly ascending."
        )
    if np.any(np.diff(latitude) <= 0):
        raise AirModelCrosscheckError(
            "Latitude coordinates must be strictly ascending."
        )

    return longitude, latitude, values


def bilinear_sample_rectilinear(
    *,
    longitude: np.ndarray,
    latitude: np.ndarray,
    values: np.ndarray,
    target_lon: float,
    target_lat: float,
) -> float | None:
    if (
        target_lon < longitude[0]
        or target_lon > longitude[-1]
        or target_lat < latitude[0]
        or target_lat > latitude[-1]
    ):
        return None

    x1_index = int(np.searchsorted(longitude, target_lon, side="right") - 1)
    y1_index = int(np.searchsorted(latitude, target_lat, side="right") - 1)

    if x1_index >= len(longitude) - 1:
        x1_index = len(longitude) - 2
    if y1_index >= len(latitude) - 1:
        y1_index = len(latitude) - 2

    x2_index = x1_index + 1
    y2_index = y1_index + 1

    x1 = float(longitude[x1_index])
    x2 = float(longitude[x2_index])
    y1 = float(latitude[y1_index])
    y2 = float(latitude[y2_index])

    q11 = values[y1_index, x1_index]
    q21 = values[y1_index, x2_index]
    q12 = values[y2_index, x1_index]
    q22 = values[y2_index, x2_index]

    corners = np.asarray([q11, q21, q12, q22], dtype=np.float64)
    if not np.isfinite(corners).all():
        return None

    if x2 == x1 or y2 == y1:
        return None

    tx = (target_lon - x1) / (x2 - x1)
    ty = (target_lat - y1) / (y2 - y1)

    value = (
        q11 * (1 - tx) * (1 - ty)
        + q21 * tx * (1 - ty)
        + q12 * (1 - tx) * ty
        + q22 * tx * ty
    )

    return float(value) if math.isfinite(float(value)) else None


def align_cams_to_geos_grid(
    cams_field: dict[str, Any],
    geos_field: dict[str, Any],
) -> dict[str, Any]:
    cams_lon, cams_lat, cams_values = _field_arrays(cams_field)
    geos_lon, geos_lat, geos_values = _field_arrays(geos_field)

    aligned_cams = np.empty_like(geos_values, dtype=np.float64)
    aligned_cams.fill(np.nan)
    comparable = np.zeros_like(geos_values, dtype=bool)

    for row_index, target_lat in enumerate(geos_lat):
        for col_index, target_lon in enumerate(geos_lon):
            geos_value = geos_values[row_index, col_index]
            if not math.isfinite(float(geos_value)):
                continue

            cams_value = bilinear_sample_rectilinear(
                longitude=cams_lon,
                latitude=cams_lat,
                values=cams_values,
                target_lon=float(target_lon),
                target_lat=float(target_lat),
            )
            if cams_value is None:
                continue

            aligned_cams[row_index, col_index] = cams_value
            comparable[row_index, col_index] = True

    difference = np.empty_like(geos_values, dtype=np.float64)
    difference.fill(np.nan)
    difference[comparable] = (
        geos_values[comparable] - aligned_cams[comparable]
    )

    return {
        "longitude": geos_lon,
        "latitude": geos_lat,
        "geos_values": geos_values,
        "cams_values_on_geos_grid": aligned_cams,
        "difference_geos_minus_cams": difference,
        "comparable_mask": comparable,
    }


def _finite_pair_metrics(
    geos_values: np.ndarray,
    cams_values: np.ndarray,
    comparable: np.ndarray,
) -> dict[str, Any]:
    geos = geos_values[comparable].astype(np.float64, copy=False)
    cams = cams_values[comparable].astype(np.float64, copy=False)

    count = int(geos.size)
    if count == 0:
        raise AirModelCrosscheckUnavailable(
            "No overlapping valid CAMS/GEOS-CF comparison points."
        )

    delta = geos - cams
    absolute = np.abs(delta)

    if count >= 2:
        geos_std = float(np.std(geos))
        cams_std = float(np.std(cams))
        if geos_std > 0 and cams_std > 0:
            pearson_r = float(np.corrcoef(geos, cams)[0, 1])
        else:
            pearson_r = None
    else:
        pearson_r = None

    denominator = (np.abs(geos) + np.abs(cams)) / 2.0
    relative_mask = denominator > 1.0e-12

    if np.any(relative_mask):
        symmetric_relative_difference_percent = float(
            np.mean(
                absolute[relative_mask]
                / denominator[relative_mask]
            )
            * 100.0
        )
    else:
        symmetric_relative_difference_percent = None

    return {
        "count": count,
        "geos_mean": float(np.mean(geos)),
        "cams_mean": float(np.mean(cams)),
        "bias_geos_minus_cams": float(np.mean(delta)),
        "mae": float(np.mean(absolute)),
        "median_absolute_difference": float(np.median(absolute)),
        "rmse": float(np.sqrt(np.mean(delta ** 2))),
        "pearson_r": pearson_r,
        "symmetric_mean_absolute_relative_difference_percent":
            symmetric_relative_difference_percent,
    }


def _matrix_to_json(values: np.ndarray) -> list[list[float | None]]:
    output: list[list[float | None]] = []
    for row in values:
        output.append(
            [
                float(value) if math.isfinite(float(value)) else None
                for value in row
            ]
        )
    return output


def build_model_crosscheck(
    *,
    cams_field: dict[str, Any],
    geos_field: dict[str, Any],
    max_time_gap_minutes: float = 45.0,
) -> dict[str, Any]:
    product = str(geos_field.get("product", "")).lower()
    if product not in SUPPORTED_PRODUCTS:
        raise ValueError(
            "AIR-1.5C cross-check currently supports pm25 and pm10 only."
        )

    cams_units_raw = _extract_units(cams_field)
    geos_units_raw = _extract_units(geos_field)

    cams_units = _normalize_unit_text(cams_units_raw)
    geos_units = _normalize_unit_text(geos_units_raw)

    if not cams_units or not geos_units:
        raise AirModelCrosscheckError(
            "Unable to resolve model units: "
            f"CAMS={cams_units_raw!r}, GEOS-CF={geos_units_raw!r}."
        )

    if cams_units != geos_units:
        raise AirModelCrosscheckError(
            "Unit mismatch after normalization: "
            f"CAMS={cams_units_raw!r}, GEOS-CF={geos_units_raw!r}."
        )

    geos_valid = _parse_utc(str(geos_field["valid_time"]))
    cams_valid = _parse_utc(str(cams_field["valid_time"]))

    time_gap_minutes = abs(
        (cams_valid - geos_valid).total_seconds()
    ) / 60.0

    if time_gap_minutes > float(max_time_gap_minutes):
        raise AirModelCrosscheckUnavailable(
            "CAMS and GEOS-CF valid times exceed allowed gap: "
            f"{time_gap_minutes:.1f} min > "
            f"{float(max_time_gap_minutes):.1f} min."
        )

    aligned = align_cams_to_geos_grid(
        cams_field,
        geos_field,
    )

    metrics = _finite_pair_metrics(
        aligned["geos_values"],
        aligned["cams_values_on_geos_grid"],
        aligned["comparable_mask"],
    )

    total_geos_points = int(aligned["geos_values"].size)
    compared_points = int(metrics["count"])

    return {
        "kind": "model_crosscheck",
        "product": product,
        "units": geos_units_raw,
        "unit_alignment": {
            "cams_raw": cams_units_raw,
            "geos_cf_raw": geos_units_raw,
            "canonical": cams_units,
            "status": "compatible",
        },
        "semantics": {
            "observation": False,
            "model_forecast_comparison": True,
            "models": [
                "CAMS Europe ensemble",
                "NASA GEOS-CF v2",
            ],
            "agreement_classification": "not_calibrated",
            "warning": (
                "This stage reports aligned model-to-model metrics only. "
                "It does not classify either model as ground truth and does "
                "not yet apply agreement/disagreement thresholds."
            ),
        },
        "time_alignment": {
            "geos_valid_time": _utc_iso(geos_valid),
            "cams_valid_time": _utc_iso(cams_valid),
            "absolute_gap_minutes": float(time_gap_minutes),
            "max_allowed_gap_minutes": float(max_time_gap_minutes),
            "status": "aligned",
        },
        "spatial_alignment": {
            "reference_grid": "GEOS-CF v2",
            "method": "bilinear_interpolate_CAMS_to_GEOS_centres",
            "interpolation_missing_policy": (
                "skip target when any CAMS interpolation corner is invalid"
            ),
            "geos_grid_width": int(len(aligned["longitude"])),
            "geos_grid_height": int(len(aligned["latitude"])),
            "total_geos_points": total_geos_points,
            "compared_points": compared_points,
            "comparison_coverage_percent": (
                float(100.0 * compared_points / total_geos_points)
                if total_geos_points
                else 0.0
            ),
        },
        "metrics": metrics,
        "difference_grid": {
            "longitude": [
                float(value) for value in aligned["longitude"]
            ],
            "latitude": [
                float(value) for value in aligned["latitude"]
            ],
            "values_geos_minus_cams": _matrix_to_json(
                aligned["difference_geos_minus_cams"]
            ),
        },
        "sources": {
            "cams": {
                "provider": cams_field.get("provider"),
                "dataset": cams_field.get("dataset"),
                "model": cams_field.get("model"),
                "run_time": cams_field.get("run_time"),
                "valid_time": cams_field.get("valid_time"),
                "lead_hour": cams_field.get("lead_hour"),
                "pollutant": cams_field.get("pollutant"),
                "source_variable": _extract_source_variable(cams_field),
                "provenance": cams_field.get("provenance"),
            },
            "geos_cf": {
                "provider": geos_field.get("provider"),
                "dataset": geos_field.get("dataset"),
                "model": geos_field.get("model"),
                "run_time": geos_field.get("run_time"),
                "valid_time": geos_field.get("valid_time"),
                "forecast_time_index":
                    geos_field.get("forecast_time_index"),
                "freshness": geos_field.get("freshness"),
                "provenance": geos_field.get("provenance"),
            },
        },
    }


def fetch_time_aligned_crosscheck(
    *,
    product: str = "pm25",
    geos_time_index: int = 0,
    geos_stride: int = 1,
    cams_stride: int = 1,
    max_time_gap_minutes: float = 45.0,
    cams_service: CamsAirFieldService | None = None,
) -> dict[str, Any]:
    product_key = product.strip().lower()
    if product_key not in SUPPORTED_PRODUCTS:
        raise ValueError(
            "AIR-1.5C cross-check currently supports pm25 and pm10 only."
        )

    geos_field = fetch_geos_cf_field(
        product=product_key,
        time_index=geos_time_index,
        stride=geos_stride,
    )

    if not geos_field.get("cams_comparison", {}).get(
        "unit_compatible",
        False,
    ):
        raise AirModelCrosscheckError(
            "GEOS-CF product is not unit-compatible with CAMS."
        )

    target = nearest_cams_target(geos_field["valid_time"])

    cams_service = cams_service or CamsAirFieldService()

    cams_field = cams_service.get_field(
        pollutant=product_key,
        run_date=target["run_date"],
        lead_hour=int(target["lead_hour"]),
        stride=cams_stride,
    )

    return build_model_crosscheck(
        cams_field=cams_field,
        geos_field=geos_field,
        max_time_gap_minutes=max_time_gap_minutes,
    )
