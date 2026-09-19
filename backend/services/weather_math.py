from __future__ import annotations

import math


class PrecipitationSemanticsError(ValueError):
    pass


def wind_speed_ms(u_ms: float, v_ms: float) -> float:
    return math.hypot(float(u_ms), float(v_ms))


def wind_from_direction_deg(u_ms: float, v_ms: float) -> float:
    u = float(u_ms)
    v = float(v_ms)

    if math.isclose(u, 0.0, abs_tol=1e-12) and math.isclose(
        v,
        0.0,
        abs_tol=1e-12,
    ):
        return 0.0

    return math.degrees(math.atan2(-u, -v)) % 360.0


def wind_components_from_speed_direction(
    speed_ms: float,
    direction_from_deg: float,
) -> tuple[float, float]:
    speed = float(speed_ms)
    if speed < 0.0:
        raise ValueError("wind speed cannot be negative")

    direction = math.radians(float(direction_from_deg) % 360.0)
    u = -speed * math.sin(direction)
    v = -speed * math.cos(direction)
    return u, v


def precipitation_m_to_mm(value_m: float) -> float:
    value = float(value_m)
    if value < 0.0:
        raise ValueError("precipitation accumulation cannot be negative")
    return value * 1000.0


def deaccumulate_precipitation_mm(
    *,
    previous_accumulation_mm: float,
    current_accumulation_mm: float,
    interval_hours: float,
) -> tuple[float, float]:
    previous = float(previous_accumulation_mm)
    current = float(current_accumulation_mm)
    hours = float(interval_hours)

    if previous < 0.0 or current < 0.0:
        raise ValueError("precipitation accumulation cannot be negative")
    if hours <= 0.0:
        raise ValueError("interval_hours must be positive")

    interval = current - previous

    if interval < -1e-9:
        raise PrecipitationSemanticsError(
            "accumulated precipitation decreased; possible forecast-cycle reset "
            "or mixed model runs"
        )

    interval = max(0.0, interval)
    return interval, interval / hours


def normalize_longitude_180(longitude_deg: float) -> float:
    value = float(longitude_deg)
    return ((value + 180.0) % 360.0) - 180.0


def longitude_for_dataset(
    longitude_deg: float,
    *,
    dataset_uses_360: bool,
) -> float:
    lon = normalize_longitude_180(longitude_deg)
    if dataset_uses_360 and lon < 0.0:
        return lon + 360.0
    return lon
