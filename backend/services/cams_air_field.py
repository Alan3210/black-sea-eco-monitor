from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
from typing import Any

import numpy as np
import xarray as xr

from backend.services.cams_air_quality_provider import (
    CAMS_DATASET,
    CAMS_MODEL,
    CAMS_PRODUCT_TYPE,
    DEFAULT_BLACK_SEA_AREA,
    DEFAULT_CACHE_DIR,
    POLLUTANTS,
    CamsEuropeAirQualityProvider,
    CamsRequestError,
    default_operational_run_date,
)


VARIABLE_ALIASES = {
    "pm25": (
        "pm2p5_conc",
        "pm25_conc",
    ),
    "pm10": (
        "pm10_conc",
    ),
    "no2": (
        "no2_conc",
    ),
    "so2": (
        "so2_conc",
    ),
    "o3": (
        "o3_conc",
    ),
    "dust": (
        "dust_conc",
    ),
}


class CamsAirFieldError(RuntimeError):
    """Base error for canonical CAMS air-field extraction."""


class CamsAirFieldUnavailable(CamsAirFieldError):
    """Raised when a requested field cannot be found or retrieved."""


class CamsAirFieldSchemaError(CamsAirFieldError):
    """Raised when a CAMS artifact has an unexpected schema."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_pollutant(
    pollutant: str,
) -> str:
    canonical = pollutant.strip().lower()

    if canonical not in POLLUTANTS:
        raise CamsRequestError(
            f"Unsupported CAMS pollutant: {pollutant!r}"
        )

    return canonical


def normalize_stride(
    stride: int,
) -> int:
    value = int(stride)

    if value < 1 or value > 8:
        raise CamsRequestError(
            "Air-field stride must be within 1..8."
        )

    return value


def operational_lead_hour(
    run_date: date,
    now_utc: datetime | None = None,
) -> int:
    now = (
        now_utc
        or _utc_now()
    ).astimezone(timezone.utc)

    run_start = datetime.combine(
        run_date,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    hours = int(
        (
            now.replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            - run_start
        ).total_seconds()
        // 3600
    )

    return max(
        0,
        min(
            96,
            hours,
        ),
    )


def _metadata_for_netcdf(
    netcdf_path: Path,
) -> dict[str, Any]:
    metadata_path = (
        netcdf_path.parent.parent
        / "metadata.json"
    )

    if not metadata_path.exists():
        return {}

    try:
        return json.loads(
            metadata_path.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}


def find_cached_cams_netcdf(
    *,
    run_date: date | str,
    pollutant: str,
    lead_hour: int,
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
) -> Path | None:
    run = (
        run_date.isoformat()
        if isinstance(run_date, date)
        else str(run_date)
    )

    root = (
        Path(cache_dir)
        / run
    )

    if not root.exists():
        return None

    candidates: list[Path] = []

    for path in root.rglob("*.nc"):
        metadata = _metadata_for_netcdf(
            path
        )

        if not metadata:
            continue

        pollutants = metadata.get(
            "pollutants",
            [],
        )

        leads = [
            int(value)
            for value in metadata.get(
                "lead_hours",
                [],
            )
        ]

        if (
            pollutant in pollutants
            and lead_hour in leads
        ):
            candidates.append(
                path
            )

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path:
            path.stat().st_mtime,
    )


def _variable_matches_pollutant(
    name: str,
    array: xr.DataArray,
    pollutant: str,
) -> bool:
    if name in VARIABLE_ALIASES[
        pollutant
    ]:
        return True

    species = str(
        array.attrs.get(
            "species",
            "",
        )
    ).lower()

    standard_name = str(
        array.attrs.get(
            "standard_name",
            "",
        )
    ).lower()

    aliases = {
        "pm25": (
            "pm2.5",
            "pm2p5",
        ),
        "pm10": (
            "pm10",
        ),
        "no2": (
            "nitrogen dioxide",
            "nitrogen_dioxide",
        ),
        "so2": (
            "sulphur dioxide",
            "sulfur dioxide",
            "sulphur_dioxide",
            "sulfur_dioxide",
        ),
        "o3": (
            "ozone",
        ),
        "dust": (
            "dust",
        ),
    }[pollutant]

    return any(
        alias in species
        or alias in standard_name
        for alias in aliases
    )


def detect_pollutant_variable(
    dataset: xr.Dataset,
    pollutant: str,
) -> str:
    canonical = normalize_pollutant(
        pollutant
    )

    for name in dataset.data_vars:
        if _variable_matches_pollutant(
            name,
            dataset[name],
            canonical,
        ):
            return name

    raise CamsAirFieldSchemaError(
        "Unable to find CAMS variable for "
        f"{canonical!r}. Available variables: "
        + ", ".join(
            dataset.data_vars
        )
    )


def _coordinate_name(
    dataset: xr.Dataset,
    candidates: tuple[str, ...],
) -> str:
    lookup = {
        name.lower(): name
        for name in (
            list(dataset.coords)
            + list(dataset.dims)
        )
    }

    for candidate in candidates:
        if candidate in lookup:
            return lookup[
                candidate
            ]

    raise CamsAirFieldSchemaError(
        "Missing expected coordinate: "
        + "/".join(candidates)
    )


def _canonical_valid_time(
    run_date: date,
    lead_hour: int,
) -> str:
    return (
        datetime.combine(
            run_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        + timedelta(
            hours=lead_hour
        )
    ).isoformat()


def _select_lead(
    array: xr.DataArray,
    *,
    time_name: str,
    lead_hour: int,
) -> xr.DataArray:
    values = np.asarray(
        array.coords[
            time_name
        ].values
    ).reshape(-1)

    if values.size == 0:
        raise CamsAirFieldSchemaError(
            "CAMS time coordinate is empty."
        )

    numeric = values.astype(
        float
    )

    matches = np.where(
        np.isclose(
            numeric,
            float(lead_hour),
            atol=1e-6,
        )
    )[0]

    if not matches.size:
        raise CamsAirFieldUnavailable(
            f"CAMS artifact does not contain lead {lead_hour} h."
        )

    return array.isel(
        {
            time_name:
                int(
                    matches[0]
                )
        }
    )


def extract_canonical_air_field(
    *,
    netcdf_path: Path | str,
    pollutant: str,
    run_date: date | str,
    lead_hour: int,
    stride: int = 2,
) -> dict[str, Any]:
    path = Path(
        netcdf_path
    )

    if not path.exists():
        raise CamsAirFieldUnavailable(
            f"CAMS NetCDF not found: {path}"
        )

    canonical_pollutant = (
        normalize_pollutant(
            pollutant
        )
    )

    normalized_stride = (
        normalize_stride(
            stride
        )
    )

    normalized_run_date = (
        run_date
        if isinstance(run_date, date)
        else date.fromisoformat(
            str(run_date)
        )
    )

    dataset = xr.open_dataset(
        path
    )

    try:
        variable_name = (
            detect_pollutant_variable(
                dataset,
                canonical_pollutant,
            )
        )

        lat_name = _coordinate_name(
            dataset,
            (
                "latitude",
                "lat",
            ),
        )

        lon_name = _coordinate_name(
            dataset,
            (
                "longitude",
                "lon",
            ),
        )

        time_name = _coordinate_name(
            dataset,
            (
                "time",
                "valid_time",
                "forecast_period",
                "leadtime",
                "step",
            ),
        )

        array = dataset[
            variable_name
        ]

        array = _select_lead(
            array,
            time_name=time_name,
            lead_hour=int(
                lead_hour
            ),
        )

        if "level" in array.dims:
            if array.sizes[
                "level"
            ] != 1:
                raise CamsAirFieldSchemaError(
                    "AIR-1.3B expects one CAMS surface level."
                )

            array = array.isel(
                level=0
            )

        array = array.transpose(
            lat_name,
            lon_name,
        )

        latitudes = np.asarray(
            array.coords[
                lat_name
            ].values,
            dtype=float,
        )

        longitudes = np.asarray(
            array.coords[
                lon_name
            ].values,
            dtype=float,
        )

        values = np.asarray(
            array.values,
            dtype=float,
        )

        if (
            latitudes.size > 1
            and latitudes[0]
            > latitudes[-1]
        ):
            latitudes = latitudes[
                ::-1
            ]
            values = values[
                ::-1,
                :
            ]

        if (
            longitudes.size > 1
            and longitudes[0]
            > longitudes[-1]
        ):
            longitudes = longitudes[
                ::-1
            ]
            values = values[
                :,
                ::-1
            ]

        latitudes = latitudes[
            ::normalized_stride
        ]
        longitudes = longitudes[
            ::normalized_stride
        ]
        values = values[
            ::normalized_stride,
            ::normalized_stride,
        ]

        finite = np.isfinite(
            values
        )

        if not finite.any():
            raise CamsAirFieldUnavailable(
                "CAMS field contains no finite values."
            )

        finite_values = values[
            finite
        ]

        metadata = _metadata_for_netcdf(
            path
        )

        units = str(
            array.attrs.get(
                "units",
                POLLUTANTS[
                    canonical_pollutant
                ]["units"],
            )
        )

        grid_values = [
            [
                (
                    None
                    if not np.isfinite(
                        value
                    )
                    else float(
                        value
                    )
                )
                for value in row
            ]
            for row in values
        ]

        run_time = datetime.combine(
            normalized_run_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        ).isoformat()

        return {
            "provider":
                "Copernicus Atmosphere Monitoring Service",
            "dataset": CAMS_DATASET,
            "model": CAMS_MODEL,
            "product_type":
                CAMS_PRODUCT_TYPE,
            "semantics": {
                "kind":
                    "model_forecast",
                "observation":
                    False,
                "station_measurement":
                    False,
            },
            "pollutant": {
                "id":
                    canonical_pollutant,
                "label":
                    POLLUTANTS[
                        canonical_pollutant
                    ]["label"],
                "units":
                    units,
                "quality_status":
                    POLLUTANTS[
                        canonical_pollutant
                    ]["quality_status"],
                "source_variable":
                    variable_name,
            },
            "run_time":
                run_time,
            "lead_hour":
                int(
                    lead_hour
                ),
            "valid_time":
                _canonical_valid_time(
                    normalized_run_date,
                    int(
                        lead_hour
                    ),
                ),
            "level_m":
                0.0,
            "grid": {
                "latitude_order":
                    "ascending",
                "longitude_order":
                    "ascending",
                "stride":
                    normalized_stride,
                "latitudes": [
                    float(value)
                    for value
                    in latitudes
                ],
                "longitudes": [
                    float(value)
                    for value
                    in longitudes
                ],
                "values": grid_values,
                "shape": [
                    int(
                        values.shape[0]
                    ),
                    int(
                        values.shape[1]
                    ),
                ],
                "bbox": {
                    "south":
                        float(
                            latitudes[0]
                        ),
                    "north":
                        float(
                            latitudes[-1]
                        ),
                    "west":
                        float(
                            longitudes[0]
                        ),
                    "east":
                        float(
                            longitudes[-1]
                        ),
                },
            },
            "statistics": {
                "min":
                    float(
                        np.min(
                            finite_values
                        )
                    ),
                "max":
                    float(
                        np.max(
                            finite_values
                        )
                    ),
                "mean":
                    float(
                        np.mean(
                            finite_values
                        )
                    ),
                "finite_count":
                    int(
                        finite.sum()
                    ),
                "missing_count":
                    int(
                        finite.size
                        - finite.sum()
                    ),
            },
            "provenance": {
                "artifact":
                    str(path),
                "artifact_sha256":
                    metadata.get(
                        "artifact_sha256"
                    ),
                "fetched_at":
                    metadata.get(
                        "fetched_at"
                    ),
                "request_area_nwse":
                    metadata.get(
                        "area_nwse",
                        list(
                            DEFAULT_BLACK_SEA_AREA
                        ),
                    ),
            },
        }
    finally:
        dataset.close()


class CamsAirFieldService:
    def __init__(
        self,
        *,
        provider:
            CamsEuropeAirQualityProvider
            | None = None,
        cache_dir:
            Path
            | str = DEFAULT_CACHE_DIR,
        now_factory=_utc_now,
    ) -> None:
        self.cache_dir = Path(
            cache_dir
        )
        self.provider = (
            provider
            or CamsEuropeAirQualityProvider(
                cache_dir=self.cache_dir
            )
        )
        self.now_factory = now_factory

    def get_field(
        self,
        *,
        pollutant: str = "pm25",
        run_date: date | str | None = None,
        lead_hour: int | None = None,
        stride: int = 2,
    ) -> dict[str, Any]:
        canonical_pollutant = (
            normalize_pollutant(
                pollutant
            )
        )

        if run_date is None:
            normalized_run_date = (
                default_operational_run_date(
                    self.now_factory()
                )
            )
        elif isinstance(
            run_date,
            date,
        ):
            normalized_run_date = (
                run_date
            )
        else:
            normalized_run_date = (
                date.fromisoformat(
                    str(
                        run_date
                    )
                )
            )

        if lead_hour is None:
            normalized_lead = (
                operational_lead_hour(
                    normalized_run_date,
                    self.now_factory(),
                )
            )
        else:
            normalized_lead = int(
                lead_hour
            )

        if (
            normalized_lead < 0
            or normalized_lead > 96
        ):
            raise CamsRequestError(
                "CAMS Europe lead hour must be within 0..96."
            )

        path = find_cached_cams_netcdf(
            run_date=
                normalized_run_date,
            pollutant=
                canonical_pollutant,
            lead_hour=
                normalized_lead,
            cache_dir=
                self.cache_dir,
        )

        if path is None:
            artifact = (
                self.provider.retrieve(
                    run_date=
                        normalized_run_date,
                    lead_hours=[
                        normalized_lead
                    ],
                    pollutants=[
                        canonical_pollutant
                    ],
                )
            )

            if not artifact.extracted_files:
                raise CamsAirFieldUnavailable(
                    "CAMS provider returned no NetCDF artifact."
                )

            path = Path(
                artifact.extracted_files[
                    0
                ]
            )

        return extract_canonical_air_field(
            netcdf_path=path,
            pollutant=
                canonical_pollutant,
            run_date=
                normalized_run_date,
            lead_hour=
                normalized_lead,
            stride=
                stride,
        )
