from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping
import json
import math
import re

import numpy as np


GEOS_CF_V2_AQC_LATEST = (
    "https://opendap.nccs.nasa.gov/dods/gmao/geos-cf/v2/fcst/"
    "aqc_tavg_1hr_glo_L1440x721_slv.latest"
)

DEFAULT_BLACK_SEA_BBOX = (26.0, 39.0, 43.5, 48.0)

GLOBAL_LON_MIN = -180.0
GLOBAL_LAT_MIN = -90.0
GLOBAL_RESOLUTION_DEG = 0.25
GLOBAL_LON_COUNT = 1440
GLOBAL_LAT_COUNT = 721
FORECAST_TIME_COUNT = 120
MISSING_ABS_THRESHOLD = 1.0e14

PRODUCTS: dict[str, dict[str, Any]] = {
    "pm25": {
        "source_variable": "pm25_rh35",
        "quantity": "particulate_matter_pm2p5_mass_concentration_rh35",
        "units": "µg/m³",
        "source_units": "ug m-3",
        "direct_cams_unit_comparison": True,
        "note": "PM2.5 mass concentration at RH 35%, including aerosol water.",
    },
    "pm10": {
        "source_variable": "pm10_rh35",
        "quantity": "particulate_matter_pm10_mass_concentration_rh35",
        "units": "µg/m³",
        "source_units": "ug m-3",
        "direct_cams_unit_comparison": True,
        "note": "PM10 mass concentration at RH 35%, including aerosol water.",
    },
    "no2": {
        "source_variable": "no2",
        "quantity": "nitrogen_dioxide_mole_fraction_in_dry_air",
        "units": "mol/mol",
        "source_units": "mol mol-1",
        "direct_cams_unit_comparison": False,
        "note": "Dry-air mole fraction; conversion is required before comparison with CAMS µg/m³.",
    },
    "so2": {
        "source_variable": "so2",
        "quantity": "sulfur_dioxide_mole_fraction_in_dry_air",
        "units": "mol/mol",
        "source_units": "mol mol-1",
        "direct_cams_unit_comparison": False,
        "note": "Dry-air mole fraction; conversion is required before comparison with CAMS µg/m³.",
    },
    "o3": {
        "source_variable": "o3",
        "quantity": "ozone_mole_fraction_in_dry_air",
        "units": "mol/mol",
        "source_units": "mol mol-1",
        "direct_cams_unit_comparison": False,
        "note": "Dry-air mole fraction; conversion is required before comparison with CAMS µg/m³.",
    },
    "co": {
        "source_variable": "co",
        "quantity": "carbon_monoxide_mole_fraction_in_dry_air",
        "units": "mol/mol",
        "source_units": "mol mol-1",
        "direct_cams_unit_comparison": False,
        "note": "Dry-air mole fraction; conversion is required before mass-concentration comparison.",
    },
}


class GeosCFError(RuntimeError):
    pass


def product_info(product: str) -> dict[str, Any]:
    key = product.strip().lower()
    try:
        return dict(PRODUCTS[key])
    except KeyError as exc:
        supported = ", ".join(sorted(PRODUCTS))
        raise ValueError(
            f"Unsupported GEOS-CF product '{product}'. Supported: {supported}"
        ) from exc


def geos_cf_semantics(product: str) -> dict[str, Any]:
    info = product_info(product)
    return {
        "kind": "model_forecast",
        "provider": "NASA GMAO",
        "model": "GEOS-CF v2",
        "collection": "aqc_tavg_1hr_glo_L1440x721_slv",
        "observation": False,
        "model_forecast": True,
        "station_measurement": False,
        "satellite_observation": False,
        "surface_field": True,
        "research_product": True,
        "regulatory_compliance_product": False,
        "quantity": info["quantity"],
        "units": info["units"],
        "direct_cams_unit_comparison": info["direct_cams_unit_comparison"],
        "warning": (
            "GEOS-CF is a research atmospheric-composition model product. "
            "It is not a ground-station observation and is not a regulatory "
            "air-quality compliance measurement."
        ),
    }


def _utc_iso(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _bbox_to_indices(
    bbox: tuple[float, float, float, float],
) -> tuple[int, int, int, int]:
    if len(bbox) != 4:
        raise ValueError("bbox must be [west, south, east, north].")

    west, south, east, north = map(float, bbox)
    if not (-180 <= west <= east <= 179.75):
        raise ValueError("GEOS-CF longitude bbox must fit -180..179.75.")
    if not (-90 <= south <= north <= 90):
        raise ValueError("GEOS-CF latitude bbox must fit -90..90.")

    lon_start = math.ceil(
        (west - GLOBAL_LON_MIN) / GLOBAL_RESOLUTION_DEG - 1e-9
    )
    lon_end = math.floor(
        (east - GLOBAL_LON_MIN) / GLOBAL_RESOLUTION_DEG + 1e-9
    )
    lat_start = math.ceil(
        (south - GLOBAL_LAT_MIN) / GLOBAL_RESOLUTION_DEG - 1e-9
    )
    lat_end = math.floor(
        (north - GLOBAL_LAT_MIN) / GLOBAL_RESOLUTION_DEG + 1e-9
    )

    lon_start = max(0, min(GLOBAL_LON_COUNT - 1, lon_start))
    lon_end = max(0, min(GLOBAL_LON_COUNT - 1, lon_end))
    lat_start = max(0, min(GLOBAL_LAT_COUNT - 1, lat_start))
    lat_end = max(0, min(GLOBAL_LAT_COUNT - 1, lat_end))

    if lon_start > lon_end or lat_start > lat_end:
        raise ValueError("bbox does not contain any GEOS-CF grid centres.")

    return lon_start, lon_end, lat_start, lat_end


_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_grads_min(value: str) -> datetime:
    text = value.strip().lower()
    match = re.fullmatch(
        r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?z"
        r"(?P<day>\d{1,2})(?P<month>[a-z]{3})(?P<year>\d{4})",
        text,
    )
    if not match:
        raise ValueError(f"Unsupported GEOS-CF grads_min: {value!r}")

    month = _MONTHS.get(match.group("month"))
    if month is None:
        raise ValueError(f"Unsupported month in grads_min: {value!r}")

    return datetime(
        int(match.group("year")),
        month,
        int(match.group("day")),
        int(match.group("hour")),
        int(match.group("minute") or 0),
        tzinfo=timezone.utc,
    )


def _attrs(value: Any) -> Mapping[str, Any]:
    attrs = getattr(value, "attributes", None)
    if isinstance(attrs, Mapping):
        return attrs
    return {}


def _to_numpy(value: Any) -> np.ndarray:
    current = value

    # Pydap GridType -> BaseType -> numpy-like data.
    for attr in ("array", "data"):
        if isinstance(current, np.ndarray):
            break
        candidate = getattr(current, attr, None)
        if candidate is not None and candidate is not current:
            current = candidate

    return np.asarray(current)


def _finite_stats(values: np.ndarray) -> dict[str, Any]:
    finite = values[
        np.isfinite(values) & (np.abs(values) < MISSING_ABS_THRESHOLD)
    ]
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


def _default_opener(url: str) -> Any:
    try:
        from pydap.client import open_url
    except ImportError as exc:
        raise GeosCFError(
            "pydap is required for live GEOS-CF access. "
            "Install backend/requirements-air.txt."
        ) from exc

    try:
        return open_url(url)
    except Exception as exc:
        raise GeosCFError(
            f"Unable to open NASA GEOS-CF OPeNDAP dataset: {exc}"
        ) from exc


class GeosCFProvider:
    def __init__(
        self,
        *,
        dataset_url: str = GEOS_CF_V2_AQC_LATEST,
        cache_dir: str | Path = "data/cache/air/geos-cf-v2",
        opener: Callable[[str], Any] | None = None,
    ) -> None:
        self.dataset_url = dataset_url
        self.cache_dir = Path(cache_dir)
        self.opener = opener or _default_opener

    def _run_metadata(self, dataset: Any) -> dict[str, Any]:
        try:
            time_variable = dataset["time"]
        except Exception as exc:
            raise GeosCFError(
                "GEOS-CF dataset has no accessible time variable."
            ) from exc

        attrs = _attrs(time_variable)
        grads_min = attrs.get("grads_min")
        grads_step = attrs.get("grads_step")

        if not grads_min:
            raise GeosCFError(
                "GEOS-CF time metadata is missing grads_min."
            )

        try:
            first_valid = parse_grads_min(str(grads_min))
        except ValueError as exc:
            raise GeosCFError(str(exc)) from exc

        # GEOS-CF hourly-average files are centred on the half hour.
        # The nominal daily run is the preceding whole UTC hour.
        nominal_run = first_valid.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        return {
            "first_valid_time": first_valid,
            "run_time": nominal_run,
            "grads_min": str(grads_min),
            "grads_step": str(grads_step or "60mn"),
        }

    def fetch_field(
        self,
        *,
        product: str = "pm25",
        time_index: int = 0,
        bbox: tuple[float, float, float, float] = DEFAULT_BLACK_SEA_BBOX,
        stride: int = 1,
        force: bool = False,
    ) -> dict[str, Any]:
        info = product_info(product)
        product_key = product.strip().lower()

        if not 0 <= int(time_index) < FORECAST_TIME_COUNT:
            raise ValueError(
                f"time_index must be between 0 and {FORECAST_TIME_COUNT - 1}."
            )
        if not 1 <= int(stride) <= 8:
            raise ValueError("stride must be between 1 and 8.")

        lon_start, lon_end, lat_start, lat_end = _bbox_to_indices(bbox)

        try:
            dataset = self.opener(self.dataset_url)
        except GeosCFError:
            raise
        except Exception as exc:
            raise GeosCFError(
                f"Unable to open NASA GEOS-CF OPeNDAP dataset: {exc}"
            ) from exc

        run = self._run_metadata(dataset)
        first_valid = run["first_valid_time"]
        valid_time = first_valid + timedelta(hours=int(time_index))
        nominal_run = run["run_time"]

        fingerprint_payload = {
            "dataset_url": self.dataset_url,
            "run_time": _utc_iso(nominal_run),
            "product": product_key,
            "time_index": int(time_index),
            "bbox": list(map(float, bbox)),
            "stride": int(stride),
        }
        fingerprint = sha256(
            json.dumps(
                fingerprint_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:20]

        target_dir = (
            self.cache_dir
            / product_key
            / nominal_run.strftime("%Y%m%d_%Hz")
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        cache_path = target_dir / f"{fingerprint}.json"

        if cache_path.exists() and not force:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached["provenance"]["cache_hit"] = True
            return cached

        source_variable = info["source_variable"]

        try:
            variable = dataset[source_variable]
            lon_variable = dataset["lon"]
            lat_variable = dataset["lat"]

            data_slice = (
                slice(int(time_index), int(time_index) + 1, 1),
                slice(0, 1, 1),
                slice(lat_start, lat_end + 1, int(stride)),
                slice(lon_start, lon_end + 1, int(stride)),
            )
            lat_slice = slice(
                lat_start,
                lat_end + 1,
                int(stride),
            )
            lon_slice = slice(
                lon_start,
                lon_end + 1,
                int(stride),
            )

            values = np.squeeze(
                _to_numpy(variable[data_slice])
            ).astype(np.float64, copy=False)
            latitude = np.ravel(
                _to_numpy(lat_variable[lat_slice])
            ).astype(np.float64, copy=False)
            longitude = np.ravel(
                _to_numpy(lon_variable[lon_slice])
            ).astype(np.float64, copy=False)
        except Exception as exc:
            raise GeosCFError(
                f"Failed to read GEOS-CF variable '{source_variable}': {exc}"
            ) from exc

        expected_shape = (len(latitude), len(longitude))
        if values.shape != expected_shape:
            try:
                values = values.reshape(expected_shape)
            except ValueError as exc:
                raise GeosCFError(
                    "Unexpected GEOS-CF field shape: "
                    f"{values.shape}, expected {expected_shape}."
                ) from exc

        valid = (
            np.isfinite(values)
            & (np.abs(values) < MISSING_ABS_THRESHOLD)
        )
        stats = _finite_stats(values)

        values_json: list[list[float | None]] = []
        for row_values, row_valid in zip(values, valid):
            row: list[float | None] = []
            for value, is_valid in zip(row_values, row_valid):
                row.append(float(value) if bool(is_valid) else None)
            values_json.append(row)

        valid_count = int(np.count_nonzero(valid))
        total_count = int(valid.size)

        result = {
            "provider": "NASA GMAO",
            "model": "GEOS-CF v2",
            "dataset": "aqc_tavg_1hr_glo_L1440x721_slv.latest",
            "dataset_url": self.dataset_url,
            "product": product_key,
            "source_variable": source_variable,
            "quantity": info["quantity"],
            "units": info["units"],
            "source_units": info["source_units"],
            "product_note": info["note"],
            "semantics": geos_cf_semantics(product_key),
            "run_time": _utc_iso(nominal_run),
            "first_valid_time": _utc_iso(first_valid),
            "valid_time": _utc_iso(valid_time),
            "forecast_time_index": int(time_index),
            "lead_hours_from_nominal_run": (
                valid_time - nominal_run
            ).total_seconds() / 3600.0,
            "time_metadata": {
                "grads_min": run["grads_min"],
                "grads_step": run["grads_step"],
                "run_time_derivation": (
                    "nominal run hour inferred from first hourly-average "
                    "valid time"
                ),
            },
            "bbox": {
                "west": float(bbox[0]),
                "south": float(bbox[1]),
                "east": float(bbox[2]),
                "north": float(bbox[3]),
            },
            "grid": {
                "crs": "EPSG:4326",
                "native_global_resolution_degrees": GLOBAL_RESOLUTION_DEG,
                "stride": int(stride),
                "width": int(len(longitude)),
                "height": int(len(latitude)),
                "longitude_order": "ascending",
                "latitude_order": "ascending",
                "source_indices": {
                    "lon_start": lon_start,
                    "lon_end": lon_end,
                    "lat_start": lat_start,
                    "lat_end": lat_end,
                },
            },
            "longitude": [float(x) for x in longitude],
            "latitude": [float(y) for y in latitude],
            "values": values_json,
            "statistics": stats,
            "coverage": {
                "valid_pixel_count": valid_count,
                "total_pixel_count": total_count,
                "valid_fraction": (
                    float(valid_count / total_count)
                    if total_count
                    else 0.0
                ),
                "valid_percent": (
                    float(100.0 * valid_count / total_count)
                    if total_count
                    else 0.0
                ),
                "missing_policy": (
                    "non-finite or abs(value)>=1e14 -> null"
                ),
            },
            "provenance": {
                "cache_hit": False,
                "cache_path": str(cache_path),
                "retrieved_at": _utc_iso(datetime.now(timezone.utc)),
                "source": "NASA NCCS OPeNDAP",
                "source_collection": (
                    "GEOS-CF v2 forecast aqc hourly-average surface layer"
                ),
                "request_fingerprint": fingerprint,
            },
        }

        cache_path.write_text(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        return result
