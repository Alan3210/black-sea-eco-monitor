from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from agents.ocean_data.dynamic_forcing_validation import (
    CURRENT_DATASET_ID,
    CURRENT_VARIABLES,
    COPERNICUS_END_PADDING_HOURS,
    DEFAULT_HALF_WIDTH_DEG,
    SALINITY_DATASET_ID,
    SALINITY_VARIABLES,
    TEMPERATURE_DATASET_ID,
    TEMPERATURE_VARIABLES,
    WAVE_DATASET_ID,
    WAVE_VARIABLES,
    DynamicForcingError,
    DynamicForcingInputError,
    _download_ecmwf_steps,
    _latest_ecmwf_client_and_run,
    _make_reader,
    _open_copernicus_dynamic,
    _open_ecmwf_wind_dataset,
    build_forcing_window,
    copernicus_request_end_time,
    ecmwf_steps_for_window,
)
from agents.ocean_data.openoil_validation import (
    OpenOilValidationError,
    OpenOilValidationInputError,
    summarize_final_positions,
    summarize_mass_budget,
)


SUPPORTED_HOURS = (6, 12, 24, 48, 72)

DEFAULT_HOURS = 6
DEFAULT_PARTICLES = 100
DEFAULT_RADIUS_M = 200.0
DEFAULT_RELEASE_VOLUME_M3 = 1.0

MIN_PARTICLES = 20
MAX_PARTICLES = 2000
MAX_RADIUS_M = 10_000.0
MAX_RELEASE_VOLUME_M3 = 10_000.0

DEFAULT_TIME_STEP_SECONDS = 900
DEFAULT_OUTPUT_STEP_SECONDS = 3600


class DynamicOpenOilError(RuntimeError):
    pass


class DynamicOpenOilInputError(ValueError):
    pass


def validate_dynamic_openoil_request(
    *,
    hours: int,
    particles: int,
    radius_m: float,
    release_volume_m3: float,
    half_width_deg: float,
) -> None:
    if int(hours) not in SUPPORTED_HOURS:
        raise DynamicOpenOilInputError(
            "hours must be one of: "
            + ", ".join(
                str(value)
                for value in SUPPORTED_HOURS
            )
        )

    if not (
        MIN_PARTICLES
        <= int(particles)
        <= MAX_PARTICLES
    ):
        raise DynamicOpenOilInputError(
            f"particles must be between {MIN_PARTICLES} and {MAX_PARTICLES}."
        )

    if not (
        0
        <= float(radius_m)
        <= MAX_RADIUS_M
    ):
        raise DynamicOpenOilInputError(
            f"radius_m must be between 0 and {MAX_RADIUS_M:g}."
        )

    if not (
        0
        < float(release_volume_m3)
        <= MAX_RELEASE_VOLUME_M3
    ):
        raise DynamicOpenOilInputError(
            "release_volume_m3 must be greater than 0 and "
            f"no more than {MAX_RELEASE_VOLUME_M3:g}."
        )

    if not (
        0.25
        <= float(half_width_deg)
        <= 4.0
    ):
        raise DynamicOpenOilInputError(
            "half_width_deg must be between 0.25 and 4.0."
        )


def _haversine_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    radius_km = 6371.0088

    lon1_r = math.radians(
        float(lon1)
    )
    lat1_r = math.radians(
        float(lat1)
    )
    lon2_r = math.radians(
        float(lon2)
    )
    lat2_r = math.radians(
        float(lat2)
    )

    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r

    a = (
        math.sin(
            dlat / 2
        ) ** 2
        + math.cos(
            lat1_r
        )
        * math.cos(
            lat2_r
        )
        * math.sin(
            dlon / 2
        ) ** 2
    )

    return (
        2
        * radius_km
        * math.asin(
            math.sqrt(a)
        )
    )


def nearest_finite_ocean_cell(
    current_dataset,
    *,
    longitude: float,
    latitude: float,
) -> dict:
    """
    Find the nearest grid cell where both uo and vo are finite at the
    first available model time/depth.

    This avoids seeding a near-coast OpenOil release on a masked land cell.
    """
    try:
        import numpy as np
    except ImportError as exc:
        raise DynamicOpenOilError(
            "NumPy is required for dynamic OpenOil."
        ) from exc

    u = current_dataset[
        "uo"
    ]
    v = current_dataset[
        "vo"
    ]

    for dimension in (
        "time",
        "depth",
    ):
        if (
            dimension in u.dims
            and u.sizes[
                dimension
            ] >= 1
        ):
            u = u.isel(
                {
                    dimension: 0
                }
            )
            v = v.isel(
                {
                    dimension: 0
                }
            )

    lon_name = (
        "longitude"
        if "longitude" in u.coords
        else "lon"
    )
    lat_name = (
        "latitude"
        if "latitude" in u.coords
        else "lat"
    )

    lon_values = (
        u[lon_name]
        .values
        .reshape(-1)
    )
    lat_values = (
        u[lat_name]
        .values
        .reshape(-1)
    )

    u_values = u.values
    v_values = v.values

    if (
        u_values.ndim != 2
        or v_values.ndim != 2
    ):
        raise DynamicOpenOilError(
            "Expected a 2D surface current field after selecting time/depth."
        )

    valid = (
        np.isfinite(
            u_values
        )
        & np.isfinite(
            v_values
        )
    )

    if not valid.any():
        raise DynamicOpenOilError(
            "No finite ocean current cells were found in the forcing window."
        )

    best = None

    for lat_index, lon_index in zip(
        *np.where(
            valid
        )
    ):
        cell_lon = float(
            lon_values[
                lon_index
            ]
        )
        cell_lat = float(
            lat_values[
                lat_index
            ]
        )

        distance_km = _haversine_km(
            longitude,
            latitude,
            cell_lon,
            cell_lat,
        )

        if (
            best is None
            or distance_km
            < best[
                "distance_km"
            ]
        ):
            best = {
                "longitude": round(
                    cell_lon,
                    6,
                ),
                "latitude": round(
                    cell_lat,
                    6,
                ),
                "distance_km": round(
                    distance_km,
                    3,
                ),
                "method": (
                    "nearest_finite_dynamic_ocean_cell"
                ),
            }

    if best is None:
        raise DynamicOpenOilError(
            "Unable to resolve an ocean seed cell."
        )

    return best


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
        if np.isnat(
            value
        ):
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

    if hasattr(
        value,
        "item",
    ):
        value = value.item()

    if isinstance(
        value,
        datetime,
    ):
        parsed = value
    else:
        text = str(value)

        if text.endswith(
            "Z"
        ):
            text = (
                text[:-1]
                + "+00:00"
            )

        parsed = datetime.fromisoformat(
            text
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )
    else:
        parsed = parsed.astimezone(
            timezone.utc
        )

    return parsed.isoformat()


def _nearest_time_index(
    result,
    target_time: datetime,
) -> int:
    try:
        import numpy as np
    except ImportError as exc:
        raise DynamicOpenOilError(
            "NumPy is required for dynamic OpenOil result analysis."
        ) from exc

    times = result[
        "time"
    ].values

    target = np.datetime64(
        target_time.replace(
            tzinfo=None
        )
    )

    differences = np.abs(
        times
        - target
    )

    return int(
        differences.argmin()
    )


def _last_finite_at_or_before(
    values,
    time_index: int,
) -> float | None:
    sliced = (
        values[
            : time_index + 1
        ]
        .reshape(-1)
    )

    for raw in reversed(
        sliced
    ):
        try:
            value = float(
                raw
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if math.isfinite(
            value
        ):
            return value

    return None



def result_time_bounds(result) -> dict:
    if "time" not in result.coords:
        return {"start_time": None, "end_time": None, "time_count": 0}

    values = result["time"].values.reshape(-1)
    if len(values) == 0:
        return {"start_time": None, "end_time": None, "time_count": 0}

    return {
        "start_time": _iso_utc(values[0]),
        "end_time": _iso_utc(values[-1]),
        "time_count": len(values),
    }


def simulation_reached_requested_end(
    result,
    requested_end_time: datetime,
    *,
    tolerance_seconds: int = 60,
) -> bool:
    if "time" not in result.coords:
        return False

    values = result["time"].values.reshape(-1)
    if len(values) == 0:
        return False

    actual_end = datetime.fromisoformat(_iso_utc(values[-1]))

    requested = requested_end_time
    if requested.tzinfo is None:
        requested = requested.replace(tzinfo=timezone.utc)
    else:
        requested = requested.astimezone(timezone.utc)

    return actual_end >= requested - timedelta(seconds=tolerance_seconds)


def snapshot_at_horizon(
    result,
    *,
    start_time: datetime,
    hours: int,
) -> dict:
    target_time = (
        start_time
        + timedelta(
            hours=int(
                hours
            )
        )
    )

    time_index = _nearest_time_index(
        result,
        target_time,
    )

    actual_time_text = _iso_utc(
        result["time"].isel(time=time_index).values
    )
    actual_time = datetime.fromisoformat(actual_time_text)

    requested_target = target_time
    if requested_target.tzinfo is None:
        requested_target = requested_target.replace(tzinfo=timezone.utc)
    else:
        requested_target = requested_target.astimezone(timezone.utc)

    horizon_complete = (
        actual_time
        >= requested_target - timedelta(seconds=60)
    )

    trajectory_count = int(
        result.sizes.get(
            "trajectory",
            0,
        )
    )

    points = []

    for trajectory_index in range(
        trajectory_count
    ):
        lon_values = (
            result["lon"]
            .isel(
                trajectory=trajectory_index
            )
            .values
        )
        lat_values = (
            result["lat"]
            .isel(
                trajectory=trajectory_index
            )
            .values
        )

        lon = _last_finite_at_or_before(
            lon_values,
            time_index,
        )
        lat = _last_finite_at_or_before(
            lat_values,
            time_index,
        )

        if (
            lon is not None
            and lat is not None
        ):
            points.append(
                [
                    round(
                        lon,
                        6,
                    ),
                    round(
                        lat,
                        6,
                    ),
                ]
            )

    if points:
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
                sum(
                    longitudes
                )
                / len(
                    longitudes
                ),
                6,
            ),
            "latitude": round(
                sum(
                    latitudes
                )
                / len(
                    latitudes
                ),
                6,
            ),
        }

        bbox = {
            "west": min(
                longitudes
            ),
            "south": min(
                latitudes
            ),
            "east": max(
                longitudes
            ),
            "north": max(
                latitudes
            ),
        }
    else:
        center = None
        bbox = None

    return {
        "hours": int(hours),
        "requested_time": requested_target.isoformat(),
        "time": actual_time_text,
        "horizon_complete": horizon_complete,
        "trajectory_count": (
            trajectory_count
        ),
        "particle_count": len(
            points
        ),
        "center": center,
        "bbox": bbox,
        "points": points,
    }


def _status_counts(
    model,
) -> dict[str, int]:
    result = getattr(
        model,
        "result",
        None,
    )

    if (
        result is None
        or "status" not in result
    ):
        return {}

    meanings = (
        result["status"]
        .attrs
        .get(
            "flag_meanings",
            "",
        )
        .split()
    )
    flag_values = (
        result["status"]
        .attrs
        .get(
            "flag_values",
            [],
        )
    )

    mapping = {}

    try:
        for code, meaning in zip(
            flag_values,
            meanings,
        ):
            mapping[
                int(
                    code
                )
            ] = meaning
    except Exception:
        mapping = {}

    counts: dict[str, int] = {}

    trajectory_count = int(
        result.sizes.get(
            "trajectory",
            0,
        )
    )

    for trajectory_index in range(
        trajectory_count
    ):
        values = (
            result["status"]
            .isel(
                trajectory=trajectory_index
            )
            .values
            .reshape(-1)
        )

        last = None

        for raw in reversed(
            values
        ):
            try:
                value = float(
                    raw
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if math.isfinite(
                value
            ):
                last = int(
                    value
                )
                break

        if last is None:
            continue

        label = mapping.get(
            last,
            str(
                last
            ),
        )

        counts[
            label
        ] = counts.get(
            label,
            0,
        ) + 1

    return counts


def _requested_horizons(
    hours: int,
) -> tuple[int, ...]:
    return tuple(
        value
        for value in SUPPORTED_HOURS
        if value <= int(
            hours
        )
    )



def _status_mapping_from_model(model) -> dict[int, str]:
    categories = list(
        getattr(
            model,
            "status_categories",
            [],
        )
    )
    return {
        index: str(label)
        for index, label in enumerate(categories)
    }


def actual_deactivation_reason_counts(
    model,
) -> dict[str, int]:
    elements = getattr(
        model,
        "elements_deactivated",
        None,
    )
    if elements is None:
        return {}

    statuses = getattr(
        elements,
        "status",
        None,
    )
    if statuses is None:
        return {}

    mapping = _status_mapping_from_model(
        model
    )
    counts: dict[str, int] = {}

    for raw in statuses:
        try:
            code = int(raw)
        except (
            TypeError,
            ValueError,
        ):
            continue

        label = mapping.get(
            code,
            str(code),
        )
        counts[label] = (
            counts.get(label, 0)
            + 1
        )

    return counts


def model_runtime_state(
    model,
    *,
    seeded_particles: int,
) -> dict:
    active = int(
        model.num_elements_active()
    )
    deactivated = int(
        model.num_elements_deactivated()
    )
    scheduled = int(
        model.num_elements_scheduled()
    )

    reasons = actual_deactivation_reason_counts(
        model
    )

    all_elements_accounted = (
        active
        + deactivated
        + scheduled
        == int(seeded_particles)
    )

    all_terminal = (
        active == 0
        and scheduled == 0
        and deactivated
        == int(seeded_particles)
    )

    physical_terminal_reasons = {
        "stranded",
    }
    reason_names = set(reasons)

    physical_terminal = (
        all_terminal
        and bool(reasons)
        and reason_names.issubset(
            physical_terminal_reasons
        )
    )

    return {
        "active_elements": active,
        "deactivated_elements": deactivated,
        "scheduled_elements": scheduled,
        "seeded_elements": int(
            seeded_particles
        ),
        "all_elements_accounted": (
            all_elements_accounted
        ),
        "all_elements_terminal": (
            all_terminal
        ),
        "physical_terminal_state": (
            physical_terminal
        ),
        "deactivation_reason_counts": (
            reasons
        ),
    }


def classify_dynamic_run_completion(
    *,
    reached_requested_end: bool,
    runtime_state: dict,
) -> dict:
    if reached_requested_end:
        return {
            "forecast_complete": True,
            "completion_reason": (
                "requested_end_reached"
            ),
            "forecast_status": (
                "DYNAMIC_SCIENTIFIC_VALIDATION"
            ),
        }

    if runtime_state.get(
        "physical_terminal_state"
    ):
        return {
            "forecast_complete": True,
            "completion_reason": (
                "all_particles_physically_terminal"
            ),
            "forecast_status": (
                "DYNAMIC_SCIENTIFIC_VALIDATION_TERMINAL"
            ),
        }

    return {
        "forecast_complete": False,
        "completion_reason": (
            "stopped_early_unresolved"
        ),
        "forecast_status": (
            "DYNAMIC_SCIENTIFIC_VALIDATION_INCOMPLETE"
        ),
    }


def run_dynamic_openoil(
    *,
    longitude: float,
    latitude: float,
    at: str | datetime | None = None,
    hours: int = DEFAULT_HOURS,
    particles: int = DEFAULT_PARTICLES,
    radius_m: float = DEFAULT_RADIUS_M,
    release_volume_m3: float = DEFAULT_RELEASE_VOLUME_M3,
    oil_type: str | None = None,
    half_width_deg: float = DEFAULT_HALF_WIDTH_DEG,
) -> dict:
    """
    Run OpenOil with time-varying Black Sea currents, waves/Stokes,
    temperature, salinity and ECMWF wind.

    This is the first dynamic-forcing scientific validation. It is still
    labelled VALIDATION until we have checked several locations/horizons,
    coastline behaviour and sensitivity against the Step 2A baseline.
    """
    validate_dynamic_openoil_request(
        hours=hours,
        particles=particles,
        radius_m=radius_m,
        release_volume_m3=release_volume_m3,
        half_width_deg=half_width_deg,
    )

    window = build_forcing_window(
        longitude=longitude,
        latitude=latitude,
        at=at,
        hours=hours,
        half_width_deg=half_width_deg,
    )

    datasets = {}

    try:
        datasets[
            "current"
        ] = _open_copernicus_dynamic(
            dataset_id=CURRENT_DATASET_ID,
            variables=CURRENT_VARIABLES,
            window=window,
            include_depth=True,
        )

        datasets[
            "wave"
        ] = _open_copernicus_dynamic(
            dataset_id=WAVE_DATASET_ID,
            variables=WAVE_VARIABLES,
            window=window,
            include_depth=False,
        )

        datasets[
            "temperature"
        ] = _open_copernicus_dynamic(
            dataset_id=TEMPERATURE_DATASET_ID,
            variables=TEMPERATURE_VARIABLES,
            window=window,
            include_depth=True,
        )

        datasets[
            "salinity"
        ] = _open_copernicus_dynamic(
            dataset_id=SALINITY_DATASET_ID,
            variables=SALINITY_VARIABLES,
            window=window,
            include_depth=True,
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

        datasets[
            "wind"
        ] = _open_ecmwf_wind_dataset(
            paths=wind_paths,
            run_time=run_time,
            steps=steps,
            window=window,
        )

        readers = [
            _make_reader(
                datasets[
                    "current"
                ],
                name=(
                    "Black Sea dynamic currents"
                ),
                mapping={
                    "uo": (
                        "x_sea_water_velocity"
                    ),
                    "vo": (
                        "y_sea_water_velocity"
                    ),
                },
            ),
            _make_reader(
                datasets[
                    "wave"
                ],
                name=(
                    "Black Sea dynamic waves"
                ),
                mapping={
                    "VHM0": (
                        "sea_surface_wave_significant_height"
                    ),
                    "VSDX": (
                        "sea_surface_wave_stokes_drift_x_velocity"
                    ),
                    "VSDY": (
                        "sea_surface_wave_stokes_drift_y_velocity"
                    ),
                },
            ),
            _make_reader(
                datasets[
                    "temperature"
                ],
                name=(
                    "Black Sea dynamic temperature"
                ),
                mapping={
                    "thetao": (
                        "sea_water_temperature"
                    ),
                },
            ),
            _make_reader(
                datasets[
                    "salinity"
                ],
                name=(
                    "Black Sea dynamic salinity"
                ),
                mapping={
                    "so": (
                        "sea_water_salinity"
                    ),
                },
            ),
            _make_reader(
                datasets[
                    "wind"
                ],
                name=(
                    "ECMWF dynamic wind"
                ),
            ),
        ]

        seed = nearest_finite_ocean_cell(
            datasets[
                "current"
            ],
            longitude=longitude,
            latitude=latitude,
        )

        try:
            from opendrift.models.openoil import (
                OpenOil,
            )
        except ImportError as exc:
            raise DynamicOpenOilError(
                "OpenDrift/OpenOil is not installed."
            ) from exc

        model = OpenOil(
            loglevel=30,
            seed=0,
            weathering_model="noaa",
        )

        model.add_reader(
            readers
        )

        selected_oil_type = (
            oil_type
            if oil_type is not None
            else model.get_config(
                "seed:oil_type"
            )
        )

        if (
            selected_oil_type
            not in model.oiltypes
        ):
            raise DynamicOpenOilInputError(
                "Unknown oil_type. Use one of OpenOil.oiltypes."
            )

        model.set_config(
            "seed:oil_type",
            selected_oil_type,
        )
        model.set_config(
            "seed:m3_per_hour",
            float(
                release_volume_m3
            ),
        )

        model.set_config(
            "processes:evaporation",
            True,
        )
        model.set_config(
            "processes:emulsification",
            True,
        )
        model.set_config(
            "processes:dispersion",
            True,
        )
        model.set_config(
            "processes:biodegradation",
            False,
        )

        # First dynamic validation stays at the surface. OpenOil still
        # receives real wave/Stokes and sea-surface temperature/salinity.
        model.set_config(
            "drift:vertical_mixing",
            False,
        )
        model.set_config(
            "drift:vertical_advection",
            False,
        )
        model.set_config(
            "drift:current_uncertainty",
            0.0,
        )
        model.set_config(
            "drift:wind_uncertainty",
            0.0,
        )

        start_time = (
            window.start_time
            .astimezone(
                timezone.utc
            )
            .replace(
                tzinfo=None
            )
        )

        model.seed_elements(
            lon=seed[
                "longitude"
            ],
            lat=seed[
                "latitude"
            ],
            number=int(
                particles
            ),
            radius=float(
                radius_m
            ),
            time=start_time,
            z=0,
        )

        try:
            result = model.run(
                duration=timedelta(
                    hours=int(
                        hours
                    )
                ),
                time_step=(
                    DEFAULT_TIME_STEP_SECONDS
                ),
                time_step_output=(
                    DEFAULT_OUTPUT_STEP_SECONDS
                ),
            )
        except Exception as exc:
            raise DynamicOpenOilError(
                "Dynamic OpenOil run failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        runtime_state = model_runtime_state(
            model,
            seeded_particles=particles,
        )

        horizons = [
            snapshot_at_horizon(
                result,
                start_time=window.start_time,
                hours=horizon,
            )
            for horizon in _requested_horizons(hours)
        ]

        result_bounds = result_time_bounds(result)
        reached_requested_end = simulation_reached_requested_end(
            result,
            window.end_time,
        )

        completion = classify_dynamic_run_completion(
            reached_requested_end=(
                reached_requested_end
            ),
            runtime_state=runtime_state,
        )

        return {
            "mode": (
                "openoil_dynamic_forcing_validation"
            ),
            "forecast_status": (
                completion[
                    "forecast_status"
                ]
            ),
            "forecast_complete": (
                completion[
                    "forecast_complete"
                ]
            ),
            "completion_reason": (
                completion[
                    "completion_reason"
                ]
            ),
            "model": "OpenOil",
            "weathering_model": (
                "NOAA ADIOS"
            ),
            "oil_type": (
                selected_oil_type
            ),
            "requested_location": {
                "longitude": float(
                    longitude
                ),
                "latitude": float(
                    latitude
                ),
            },
            "model_seed_location": (
                seed
            ),
            "release": {
                "volume_m3": float(
                    release_volume_m3
                ),
                "particles": int(
                    particles
                ),
                "radius_m": float(
                    radius_m
                ),
                "release_mode": (
                    "instantaneous"
                ),
            },
            "simulation": {
                "start_time": window.start_time.isoformat(),
                "requested_end_time": window.end_time.isoformat(),
                "actual_result_start_time": result_bounds["start_time"],
                "actual_result_end_time": result_bounds["end_time"],
                "output_time_count": result_bounds["time_count"],
                "reached_requested_end": reached_requested_end,
                "hours": int(
                    hours
                ),
                "integration_step_seconds": (
                    DEFAULT_TIME_STEP_SECONDS
                ),
                "output_step_seconds": (
                    DEFAULT_OUTPUT_STEP_SECONDS
                ),
                "vertical_mixing": False,
                "current_uncertainty": 0.0,
                "wind_uncertainty": 0.0,
            },
            "runtime_state": (
                runtime_state
            ),
            "forcing": {
                "current_dataset_id": (
                    CURRENT_DATASET_ID
                ),
                "wave_dataset_id": (
                    WAVE_DATASET_ID
                ),
                "temperature_dataset_id": (
                    TEMPERATURE_DATASET_ID
                ),
                "salinity_dataset_id": (
                    SALINITY_DATASET_ID
                ),
                "wind_source": (
                    "ECMWF IFS Open Data"
                ),
                "ecmwf_run_time": (
                    run_time.isoformat()
                ),
                "ecmwf_steps": list(
                    steps
                ),
                "copernicus_request_end_time": (
                    copernicus_request_end_time(
                        window
                    ).isoformat()
                ),
                "copernicus_end_padding_hours": (
                    COPERNICUS_END_PADDING_HOURS
                ),
                "bbox": {
                    "west": window.west,
                    "south": window.south,
                    "east": window.east,
                    "north": window.north,
                },
            },
            "horizons": horizons,
            "final_positions": (
                summarize_final_positions(
                    result
                )
            ),
            "mass_budget": (
                summarize_mass_budget(
                    result
                )
            ),
            "status_counts": (
                _status_counts(
                    model
                )
            ),
            "limitations": [
                "validation has currently been checked only for a limited number of Black Sea scenarios",
                "vertical mixing is disabled in this first dynamic validation",
                "biodegradation is disabled",
                "release is instantaneous",
                "operational use requires additional coastline and sensitivity validation",
            ],
        }

    except (
        DynamicOpenOilInputError,
        DynamicForcingInputError,
        DynamicForcingError,
        OpenOilValidationInputError,
        OpenOilValidationError,
        DynamicOpenOilError,
    ):
        raise
    except Exception as exc:
        raise DynamicOpenOilError(
            "Unable to run dynamic OpenOil validation: "
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
