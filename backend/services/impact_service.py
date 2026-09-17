from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable

from backend.schemas.impact import (
    DriftImpactResponse,
    ImpactAssessment,
    ImpactPosition,
    ImpactTarget,
)


EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(
    *,
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    lat1 = math.radians(latitude_a)
    lat2 = math.radians(latitude_b)

    d_lat = math.radians(
        latitude_b - latitude_a
    )
    d_lon = math.radians(
        longitude_b - longitude_a
    )

    value = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(d_lon / 2.0) ** 2
    )

    angular = 2.0 * math.atan2(
        math.sqrt(value),
        math.sqrt(max(0.0, 1.0 - value)),
    )

    return EARTH_RADIUS_KM * angular


def _normalized_name(value: str) -> str:
    return " ".join(
        value.strip().lower().split()
    )


def _target_id(
    *,
    name: str,
    latitude: float,
    longitude: float,
) -> str:
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        name.lower(),
    ).strip("-")

    if not slug:
        slug = "location"

    fingerprint = hashlib.sha1(
        (
            f"{_normalized_name(name)}|"
            f"{latitude:.6f}|"
            f"{longitude:.6f}"
        ).encode("utf-8")
    ).hexdigest()[:10]

    return f"loc_{slug}_{fingerprint}"


def build_targets_from_event_records(
    records: Iterable[dict],
) -> list[ImpactTarget]:
    """
    v0.1 reuses geographic places already known by the canonical EventStore.

    This is intentionally not yet a complete coastline/protected-area dataset.
    Repeated event records for the same named place are deduplicated.
    """
    selected: dict[str, ImpactTarget] = {}

    for record in records:
        location = record.get("location") or {}

        name = location.get("name")
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if (
            not isinstance(name, str)
            or not name.strip()
            or latitude is None
            or longitude is None
        ):
            continue

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            continue

        if not (
            math.isfinite(latitude)
            and math.isfinite(longitude)
        ):
            continue

        key = _normalized_name(name)

        candidate = ImpactTarget(
            id=_target_id(
                name=name,
                latitude=latitude,
                longitude=longitude,
            ),
            name=name.strip(),
            type=location.get("type"),
            position=ImpactPosition(
                latitude=latitude,
                longitude=longitude,
            ),
            location_confidence=location.get(
                "confidence"
            ),
            coordinate_source=location.get(
                "source"
            ),
        )

        existing = selected.get(key)

        if existing is None:
            selected[key] = candidate
            continue

        existing_confidence = (
            existing.location_confidence
            if existing.location_confidence is not None
            else -1.0
        )
        candidate_confidence = (
            candidate.location_confidence
            if candidate.location_confidence is not None
            else -1.0
        )

        if candidate_confidence > existing_confidence:
            selected[key] = candidate

    return sorted(
        selected.values(),
        key=lambda target: (
            target.type or "",
            target.name.lower(),
        ),
    )


def _finite_forecast_points(
    horizon: dict,
) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []

    for point in horizon.get("points") or []:
        if (
            not isinstance(point, (list, tuple))
            or len(point) < 2
        ):
            continue

        try:
            longitude = float(point[0])
            latitude = float(point[1])
        except (TypeError, ValueError):
            continue

        if not (
            math.isfinite(longitude)
            and math.isfinite(latitude)
        ):
            continue

        result.append(
            (latitude, longitude)
        )

    return result


def _horizon_hours(horizon: dict) -> int | None:
    try:
        value = int(horizon.get("hours"))
    except (TypeError, ValueError):
        return None

    if value < 0:
        return None

    return value


def _distance_to_points_km(
    target: ImpactTarget,
    points: list[tuple[float, float]],
) -> float | None:
    if not points:
        return None

    return min(
        haversine_distance_km(
            latitude_a=target.position.latitude,
            longitude_a=target.position.longitude,
            latitude_b=latitude,
            longitude_b=longitude,
        )
        for latitude, longitude in points
    )


def analyze_drift_impact(
    *,
    forecast: dict,
    targets: list[ImpactTarget],
    proximity_threshold_km: float,
) -> DriftImpactResponse:
    """
    Screen known targets against OceanDrift particle positions.

    A target is "potentially_affected" when at least one forecast particle
    comes within the configured threshold at a forecast horizon.

    This is a proximity screening result, not confirmation of shoreline or
    ecological impact.
    """
    horizons = []

    for horizon in forecast.get("horizons") or []:
        hours = _horizon_hours(horizon)

        if hours is None:
            continue

        horizons.append(
            (hours, horizon)
        )

    horizons.sort(
        key=lambda item: item[0]
    )

    assessments: list[ImpactAssessment] = []

    for target in targets:
        minimum_distance_km = None
        closest_horizon_hours = None

        affected_horizons: list[int] = []
        first_exposure_hours = None
        first_exposure_time = None

        for hours, horizon in horizons:
            points = _finite_forecast_points(
                horizon
            )

            distance_km = _distance_to_points_km(
                target,
                points,
            )

            if distance_km is None:
                continue

            if (
                minimum_distance_km is None
                or distance_km < minimum_distance_km
            ):
                minimum_distance_km = distance_km
                closest_horizon_hours = hours

            if distance_km <= proximity_threshold_km:
                affected_horizons.append(hours)

                if first_exposure_hours is None:
                    first_exposure_hours = hours
                    first_exposure_time = horizon.get(
                        "time"
                    )

        assessments.append(
            ImpactAssessment(
                target=target,
                potentially_affected=bool(
                    affected_horizons
                ),
                first_exposure_hours=(
                    first_exposure_hours
                ),
                first_exposure_time=(
                    first_exposure_time
                ),
                closest_horizon_hours=(
                    closest_horizon_hours
                ),
                minimum_distance_km=(
                    round(minimum_distance_km, 3)
                    if minimum_distance_km is not None
                    else None
                ),
                affected_horizons=(
                    affected_horizons
                ),
            )
        )

    assessments.sort(
        key=lambda item: (
            not item.potentially_affected,
            (
                item.first_exposure_hours
                if item.first_exposure_hours is not None
                else 10**9
            ),
            (
                item.minimum_distance_km
                if item.minimum_distance_km is not None
                else float("inf")
            ),
            item.target.name.lower(),
        )
    )

    affected_count = sum(
        1
        for item in assessments
        if item.potentially_affected
    )

    return DriftImpactResponse(
        model_source=forecast.get("model"),
        forecast_scope=forecast.get("scope"),
        proximity_threshold_km=(
            proximity_threshold_km
        ),
        target_count=len(targets),
        potentially_affected_count=(
            affected_count
        ),
        assessments=assessments,
    )
