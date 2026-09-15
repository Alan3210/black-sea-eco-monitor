from __future__ import annotations

import math
from datetime import timedelta
from typing import Any

from agents.ocean_data.environmental_forcing import (
    get_environmental_forcing,
)


DEFAULT_HOURS = 6
DEFAULT_PARTICLES = 100
DEFAULT_RADIUS_M = 200.0
DEFAULT_RELEASE_VOLUME_M3 = 1.0
DEFAULT_TEMPERATURE_C = 20.0
DEFAULT_SALINITY_PSU = 18.0

MIN_PARTICLES = 20
MAX_PARTICLES = 2000
MAX_HOURS = 24
MAX_RADIUS_M = 10_000.0
MAX_RELEASE_VOLUME_M3 = 10_000.0


class OpenOilValidationError(RuntimeError):
    pass


class OpenOilValidationInputError(ValueError):
    pass


def validate_request(
    *,
    hours: int,
    particles: int,
    radius_m: float,
    release_volume_m3: float,
) -> None:
    if not (
        1 <= int(hours) <= MAX_HOURS
    ):
        raise OpenOilValidationInputError(
            f"hours must be between 1 and {MAX_HOURS}."
        )

    if not (
        MIN_PARTICLES
        <= int(particles)
        <= MAX_PARTICLES
    ):
        raise OpenOilValidationInputError(
            f"particles must be between {MIN_PARTICLES} and {MAX_PARTICLES}."
        )

    if not (
        0
        <= float(radius_m)
        <= MAX_RADIUS_M
    ):
        raise OpenOilValidationInputError(
            f"radius_m must be between 0 and {MAX_RADIUS_M:g}."
        )

    if not (
        0
        < float(release_volume_m3)
        <= MAX_RELEASE_VOLUME_M3
    ):
        raise OpenOilValidationInputError(
            "release_volume_m3 must be greater than 0 and "
            f"no more than {MAX_RELEASE_VOLUME_M3:g}."
        )


def select_model_seed_location(
    forcing: dict,
    requested_longitude: float,
    requested_latitude: float,
) -> dict:
    """
    Prefer the actual finite-ocean cell used by the current field.

    This prevents the engine-validation run from accidentally seeding oil
    on land when the user-selected point is very close to the coastline.
    """
    sampled = (
        forcing.get("current", {})
        .get("sampled_location", {})
    )

    longitude = sampled.get(
        "longitude",
        requested_longitude,
    )
    latitude = sampled.get(
        "latitude",
        requested_latitude,
    )

    return {
        "longitude": float(longitude),
        "latitude": float(latitude),
        "sampling_method": sampled.get(
            "method",
            "requested_point",
        ),
        "distance_from_requested_km": sampled.get(
            "distance_km",
            0.0,
        ),
    }


def build_constant_environment(
    forcing: dict,
    *,
    temperature_c: float = DEFAULT_TEMPERATURE_C,
    salinity_psu: float = DEFAULT_SALINITY_PSU,
) -> dict[str, float]:
    ready = forcing["openoil_ready_fields"]

    return {
        "x_sea_water_velocity": float(
            ready["x_sea_water_velocity"]
        ),
        "y_sea_water_velocity": float(
            ready["y_sea_water_velocity"]
        ),
        "x_wind": float(
            ready["x_wind"]
        ),
        "y_wind": float(
            ready["y_wind"]
        ),
        "sea_surface_wave_stokes_drift_x_velocity": float(
            ready[
                "sea_surface_wave_stokes_drift_x_velocity"
            ]
        ),
        "sea_surface_wave_stokes_drift_y_velocity": float(
            ready[
                "sea_surface_wave_stokes_drift_y_velocity"
            ]
        ),
        "sea_surface_wave_significant_height": float(
            ready[
                "sea_surface_wave_significant_height"
            ]
        ),
        # Provisional constants for ENGINE VALIDATION ONLY.
        # Dynamic Black Sea temperature/salinity are added in Step 2B.
        "sea_water_temperature": float(
            temperature_c
        ),
        "sea_water_salinity": float(
            salinity_psu
        ),
        "horizontal_diffusivity": 0.0,
    }


def _finite_numbers(values) -> list[float]:
    result = []

    for raw in values:
        try:
            value = float(raw)
        except (
            TypeError,
            ValueError,
        ):
            continue

        if math.isfinite(value):
            result.append(value)

    return result


def _last_finite_value(values) -> float | None:
    """
    Return the last finite value in a trajectory.

    OpenDrift commonly stores NaN after an element becomes inactive/deactivated,
    so looking only at the final global output time silently drops trajectories
    that finished earlier.
    """
    flattened = values.reshape(-1)

    for raw in reversed(flattened):
        try:
            value = float(raw)
        except (
            TypeError,
            ValueError,
        ):
            continue

        if math.isfinite(value):
            return value

    return None


def _last_finite_pair(
    longitudes,
    latitudes,
) -> tuple[float, float] | None:
    count = min(
        len(longitudes),
        len(latitudes),
    )

    for index in range(
        count - 1,
        -1,
        -1,
    ):
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

        if (
            math.isfinite(longitude)
            and math.isfinite(latitude)
        ):
            return (
                longitude,
                latitude,
            )

    return None


def summarize_final_positions(
    result,
) -> dict:
    if "lon" not in result or "lat" not in result:
        return {
            "trajectory_count": 0,
            "particle_count": 0,
            "center": None,
            "bbox": None,
        }

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
            .reshape(-1)
        )
        lat_values = (
            result["lat"]
            .isel(
                trajectory=trajectory_index
            )
            .values
            .reshape(-1)
        )

        pair = _last_finite_pair(
            lon_values,
            lat_values,
        )

        if pair is not None:
            points.append(pair)

    if not points:
        return {
            "trajectory_count": trajectory_count,
            "particle_count": 0,
            "center": None,
            "bbox": None,
        }

    longitudes = [
        point[0]
        for point in points
    ]
    latitudes = [
        point[1]
        for point in points
    ]

    return {
        "trajectory_count": trajectory_count,
        "particle_count": len(
            points
        ),
        "center": {
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
        },
        "bbox": {
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
        },
    }


def _last_values_by_trajectory(
    result,
    variable: str,
) -> list[float]:
    if variable not in result:
        return []

    trajectory_count = int(
        result.sizes.get(
            "trajectory",
            0,
        )
    )

    values: list[float] = []

    for trajectory_index in range(
        trajectory_count
    ):
        trajectory_values = (
            result[variable]
            .isel(
                trajectory=trajectory_index
            )
            .values
            .reshape(-1)
        )

        value = _last_finite_value(
            trajectory_values
        )

        if value is not None:
            values.append(value)

    return values


def _first_values_by_trajectory(
    result,
    variable: str,
) -> list[float]:
    if variable not in result:
        return []

    trajectory_count = int(
        result.sizes.get(
            "trajectory",
            0,
        )
    )

    values: list[float] = []

    for trajectory_index in range(
        trajectory_count
    ):
        trajectory_values = (
            result[variable]
            .isel(
                trajectory=trajectory_index
            )
            .values
            .reshape(-1)
        )

        for raw in trajectory_values:
            try:
                value = float(raw)
            except (
                TypeError,
                ValueError,
            ):
                continue

            if math.isfinite(value):
                values.append(value)
                break

    return values


def _sum_last_by_trajectory(
    result,
    variable: str,
) -> float | None:
    values = _last_values_by_trajectory(
        result,
        variable,
    )

    if not values:
        return None

    return float(
        sum(values)
    )


def _mean_last_by_trajectory(
    result,
    variable: str,
) -> float | None:
    values = _last_values_by_trajectory(
        result,
        variable,
    )

    if not values:
        return None

    return float(
        sum(values)
        / len(values)
    )


def summarize_mass_budget(
    result,
) -> dict:
    initial_values = (
        _first_values_by_trajectory(
            result,
            "mass_oil",
        )
    )

    initial = (
        float(
            sum(initial_values)
        )
        if initial_values
        else None
    )

    remaining = (
        _sum_last_by_trajectory(
            result,
            "mass_oil",
        )
    )
    evaporated = (
        _sum_last_by_trajectory(
            result,
            "mass_evaporated",
        )
    )
    dispersed = (
        _sum_last_by_trajectory(
            result,
            "mass_dispersed",
        )
    )
    biodegraded = (
        _sum_last_by_trajectory(
            result,
            "mass_biodegraded",
        )
    )

    components = [
        value
        for value in (
            remaining,
            evaporated,
            dispersed,
            biodegraded,
        )
        if value is not None
    ]

    accounted = (
        sum(components)
        if components
        else None
    )

    closure_error = None
    closure_error_percent = None

    if (
        initial is not None
        and accounted is not None
    ):
        closure_error = (
            accounted - initial
        )

        if abs(initial) > 1e-12:
            closure_error_percent = (
                closure_error
                / initial
                * 100.0
            )

    return {
        "initial_oil_kg": (
            None
            if initial is None
            else round(
                initial,
                3,
            )
        ),
        "remaining_oil_kg": (
            None
            if remaining is None
            else round(
                remaining,
                3,
            )
        ),
        "evaporated_kg": (
            None
            if evaporated is None
            else round(
                evaporated,
                3,
            )
        ),
        "dispersed_kg": (
            None
            if dispersed is None
            else round(
                dispersed,
                3,
            )
        ),
        "biodegraded_kg": (
            None
            if biodegraded is None
            else round(
                biodegraded,
                3,
            )
        ),
        "accounted_mass_kg": (
            None
            if accounted is None
            else round(
                accounted,
                3,
            )
        ),
        "mass_closure_error_kg": (
            None
            if closure_error is None
            else round(
                closure_error,
                6,
            )
        ),
        "mass_closure_error_percent": (
            None
            if closure_error_percent is None
            else round(
                closure_error_percent,
                6,
            )
        ),
        "mean_water_fraction": (
            _mean_last_by_trajectory(
                result,
                "water_fraction",
            )
        ),
        "mean_fraction_evaporated": (
            _mean_last_by_trajectory(
                result,
                "fraction_evaporated",
            )
        ),
        "trajectories_with_mass": len(
            _last_values_by_trajectory(
                result,
                "mass_oil",
            )
        ),
    }


def _status_summary(
    model,
) -> dict[str, int]:
    result = getattr(
        model,
        "result",
        None,
    )

    if result is None or "status" not in result:
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

    values = (
        result["status"]
        .attrs
        .get(
            "flag_values",
            [],
        )
    )

    mapping = {}

    try:
        for value, meaning in zip(
            values,
            meanings,
        ):
            mapping[
                int(value)
            ] = meaning
    except Exception:
        mapping = {}

    trajectory_count = int(
        result.sizes.get(
            "trajectory",
            0,
        )
    )

    summary: dict[str, int] = {}

    for trajectory_index in range(
        trajectory_count
    ):
        trajectory_status = (
            result["status"]
            .isel(
                trajectory=trajectory_index
            )
            .values
            .reshape(-1)
        )

        last_status = _last_finite_value(
            trajectory_status
        )

        if last_status is None:
            continue

        code = int(
            last_status
        )

        label = mapping.get(
            code,
            str(code),
        )

        summary[label] = (
            summary.get(
                label,
                0,
            )
            + 1
        )

    return summary


def run_openoil_engine_validation(
    *,
    longitude: float,
    latitude: float,
    at: str | None = None,
    hours: int = DEFAULT_HOURS,
    particles: int = DEFAULT_PARTICLES,
    radius_m: float = DEFAULT_RADIUS_M,
    release_volume_m3: float = DEFAULT_RELEASE_VOLUME_M3,
    oil_type: str | None = None,
    temperature_c: float = DEFAULT_TEMPERATURE_C,
    salinity_psu: float = DEFAULT_SALINITY_PSU,
) -> dict:
    """
    Run OpenOil with a single, real environmental forcing snapshot held
    constant through the simulation.

    This validates:
      - OpenOil engine
      - NOAA ADIOS oil properties
      - oil weathering
      - wind/current/Stokes coupling
      - mass-budget extraction

    It is deliberately NOT called an operational forecast because the
    forcing is constant in space/time during the validation run.
    """
    validate_request(
        hours=hours,
        particles=particles,
        radius_m=radius_m,
        release_volume_m3=release_volume_m3,
    )

    forcing = get_environmental_forcing(
        longitude=longitude,
        latitude=latitude,
        at=at,
    )

    seed = select_model_seed_location(
        forcing,
        requested_longitude=longitude,
        requested_latitude=latitude,
    )

    environment = build_constant_environment(
        forcing,
        temperature_c=temperature_c,
        salinity_psu=salinity_psu,
    )

    try:
        from opendrift.models.openoil import OpenOil
        from opendrift.readers.reader_constant import (
            Reader as ConstantReader,
        )
    except ImportError as exc:
        raise OpenOilValidationError(
            "OpenDrift/OpenOil is not installed."
        ) from exc

    model = OpenOil(
        loglevel=30,
        seed=0,
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
        raise OpenOilValidationInputError(
            "Unknown oil_type. Use one of the values from OpenOil.oiltypes."
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

    # Keep this first validation run at the surface. Dynamic vertical
    # mixing is enabled later together with true temperature/salinity
    # profiles and time-varying forcing.
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

    reader = ConstantReader(
        environment
    )
    model.add_reader(
        reader
    )

    start_time_text = forcing[
        "target_time"
    ]

    from datetime import datetime

    start_time = datetime.fromisoformat(
        start_time_text
    )

    # OpenDrift internally uses naive UTC datetimes for many readers/models.
    if start_time.tzinfo is not None:
        start_time = start_time.replace(
            tzinfo=None
        )

    model.seed_elements(
        lon=seed["longitude"],
        lat=seed["latitude"],
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
            time_step=900,
            time_step_output=3600,
        )
    except Exception as exc:
        raise OpenOilValidationError(
            "OpenOil engine validation failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    final_positions = (
        summarize_final_positions(
            result
        )
    )
    mass_budget = (
        summarize_mass_budget(
            result
        )
    )

    return {
        "mode": (
            "openoil_engine_validation_constant_forcing"
        ),
        "forecast_status": (
            "NOT_OPERATIONAL_FORECAST"
        ),
        "model": "OpenOil",
        "weathering_model": "NOAA ADIOS",
        "oil_type": selected_oil_type,
        "requested_location": {
            "longitude": float(
                longitude
            ),
            "latitude": float(
                latitude
            ),
        },
        "model_seed_location": seed,
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
        },
        "simulation": {
            "hours": int(
                hours
            ),
            "integration_step_seconds": 900,
            "output_step_seconds": 3600,
            "vertical_mixing": False,
            "current_uncertainty": 0.0,
            "wind_uncertainty": 0.0,
        },
        "forcing_snapshot": {
            "target_time": forcing[
                "target_time"
            ],
            "current": forcing[
                "current"
            ],
            "wave": forcing[
                "wave"
            ],
            "wind": forcing[
                "wind"
            ],
            "temperature_c": float(
                temperature_c
            ),
            "salinity_psu": float(
                salinity_psu
            ),
            "forcing_semantics": (
                "real start-time snapshot held constant in space/time"
            ),
        },
        "processes": {
            "evaporation": True,
            "emulsification": True,
            "dispersion": True,
            "biodegradation": False,
        },
        "final_positions": final_positions,
        "mass_budget": mass_budget,
        "status_counts": (
            _status_summary(
                model
            )
        ),
        "limitations": [
            "currents are constant in space and time during this validation run",
            "wind is constant in space and time during this validation run",
            "waves and Stokes drift are constant in space and time during this validation run",
            "sea-water temperature is a provisional constant",
            "sea-water salinity is a provisional constant",
            "vertical mixing is disabled",
            "this result must not be presented as an operational oil-spill forecast",
        ],
    }
