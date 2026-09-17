from __future__ import annotations

from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt
from typing import Iterable

from backend.schemas.ar import (
    ARObject,
    ARPosition,
    ARScene,
    ARVisual,
)


EARTH_RADIUS_M = 6_371_000.0

DEFAULT_DEMO_LATITUDE = 44.7240
DEFAULT_DEMO_LONGITUDE = 37.7691

HUD_CENTER_HALF_ANGLE_DEG = 12.0
NEAR_DISTANCE_M = 1_000.0
MEDIUM_DISTANCE_M = 10_000.0

# At effectively the same observer position, azimuth is undefined.
# Treat it as centered in the HUD rather than deriving a fake left/right hint
# from the device heading.
COLOCATED_DISTANCE_EPSILON_M = 1.0

CATEGORY_ICON_MAP = {
    "oil_spill": "oil_spill",
    "wildfire": "wildfire",
    "industrial_fire": "industrial_fire",
    "water_pollution": "water_pollution",
    "algae_bloom": "algae_bloom",
    "marine_animal_death": "marine_animal_death",
    "chemical_release": "chemical_release",
    "storm_damage": "storm_damage",
}

VALID_PRIORITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _normalize_priority(value: str | None) -> str:
    if value in VALID_PRIORITIES:
        return value
    return "medium"


def _fallback_title(category: str | None) -> str:
    if category == "oil_spill":
        return "Нефтяное загрязнение"
    if category == "wildfire":
        return "Природный пожар"
    if category == "industrial_fire":
        return "Промышленный пожар"
    if category == "water_pollution":
        return "Загрязнение воды"
    if category == "algae_bloom":
        return "Цветение водорослей"
    if category == "marine_animal_death":
        return "Гибель морских животных"
    if category == "chemical_release":
        return "Химический выброс"
    if category == "storm_damage":
        return "Штормовое воздействие"
    return "Экологическое событие"


def calculate_distance_and_bearing(
    observer: ARPosition,
    target: ARPosition,
) -> tuple[float, float]:
    """
    Return great-circle distance in metres and initial bearing in degrees.

    Bearing convention:
    0° = north, 90° = east, 180° = south, 270° = west.

    For exactly co-located points, the mathematical bearing is undefined;
    this function returns 0° for backwards compatibility. HUD logic handles
    co-located objects explicitly.
    """
    lat1 = radians(observer.latitude)
    lon1 = radians(observer.longitude)
    lat2 = radians(target.latitude)
    lon2 = radians(target.longitude)

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    haversine_a = (
        sin(d_lat / 2.0) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(d_lon / 2.0) ** 2
    )

    angular_distance = 2.0 * atan2(
        sqrt(haversine_a),
        sqrt(max(0.0, 1.0 - haversine_a)),
    )

    distance_m = EARTH_RADIUS_M * angular_distance

    if distance_m < 0.001:
        bearing_deg = 0.0
    else:
        y = sin(d_lon) * cos(lat2)
        x = (
            cos(lat1) * sin(lat2)
            - sin(lat1) * cos(lat2) * cos(d_lon)
        )
        bearing_deg = (
            atan2(y, x) * 180.0 / 3.141592653589793
            + 360.0
        ) % 360.0

    return distance_m, bearing_deg


def calculate_relative_angle(
    bearing_deg: float,
    heading_deg: float,
) -> float:
    """
    Signed shortest angular offset from camera/device heading to target.

    Negative = left of heading.
    Positive = right of heading.
    Range = [-180, 180].
    """
    value = (
        (bearing_deg - heading_deg + 540.0)
        % 360.0
    ) - 180.0

    if value == -180.0:
        return 180.0

    return value


def distance_label(distance_m: float) -> str:
    """
    Produce a compact human-readable label for the HUD.
    """
    if distance_m < 1_000.0:
        return f"{int(round(distance_m))} m"

    distance_km = distance_m / 1_000.0

    if distance_km < 10.0:
        return f"{distance_km:.1f} km"

    return f"{int(round(distance_km))} km"


def distance_tier(distance_m: float) -> str:
    if distance_m <= NEAR_DISTANCE_M:
        return "near"

    if distance_m <= MEDIUM_DISTANCE_M:
        return "medium"

    return "far"


def direction_hint(relative_angle_deg: float | None) -> str | None:
    if relative_angle_deg is None:
        return None

    if abs(relative_angle_deg) <= HUD_CENTER_HALF_ANGLE_DEG:
        return "center"

    if relative_angle_deg < 0.0:
        return "left"

    return "right"


def _apply_observer_metrics(
    ar_object: ARObject,
    observer: ARPosition,
    heading_deg: float | None,
) -> ARObject:
    distance_m, bearing_deg = calculate_distance_and_bearing(
        observer,
        ar_object.position,
    )

    relative_angle_deg = None
    hud_direction_hint = None

    if distance_m <= COLOCATED_DISTANCE_EPSILON_M:
        # Direction has no useful meaning when observer and object occupy
        # effectively the same position. Keep the object centered.
        if heading_deg is not None:
            relative_angle_deg = 0.0
            hud_direction_hint = "center"
    elif heading_deg is not None:
        relative_angle_deg = calculate_relative_angle(
            bearing_deg,
            heading_deg,
        )
        hud_direction_hint = direction_hint(
            relative_angle_deg
        )

    return ar_object.model_copy(
        update={
            "distance_m": round(distance_m, 2),
            "bearing_deg": round(bearing_deg, 2),
            "distance_label": distance_label(distance_m),
            "distance_tier": distance_tier(distance_m),
            "relative_angle_deg": (
                round(relative_angle_deg, 2)
                if relative_angle_deg is not None
                else None
            ),
            "direction_hint": hud_direction_hint,
        }
    )


def event_record_to_ar_object(record: dict) -> ARObject | None:
    """
    Convert one canonical EventStore record to an AR incident.

    Events without valid coordinates are skipped because they cannot be
    placed in geospatial AR.
    """
    location = record.get("location") or {}

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        return None

    category = record.get("category")
    severity = record.get("severity")

    time_data = record.get("time") or {}
    incident_time = time_data.get("incident_time")
    detection_time = time_data.get("detection_time")
    source_time = time_data.get("source_time")

    title = record.get("primary_title")
    if not isinstance(title, str) or not title.strip():
        title = _fallback_title(category)

    return ARObject(
        id=str(record["id"]),
        type="incident",
        category=category,
        position=ARPosition(
            latitude=float(latitude),
            longitude=float(longitude),
        ),
        visual=ARVisual(
            icon=CATEGORY_ICON_MAP.get(
                category,
                "environmental_event",
            ),
            priority=_normalize_priority(severity),
        ),
        title=title.strip(),
        source="EventStore",
        observed_at=incident_time or detection_time,
        status=record.get("status"),
        confidence=record.get("confidence"),
        location_name=location.get("name"),
        location_type=location.get("type"),
        location_confidence=location.get("confidence"),
        coordinate_source=location.get("source"),
        incident_time=incident_time,
        detection_time=detection_time,
        source_time=source_time,
        evidence_count=record.get("evidence_count"),
    )


def _demo_current_object() -> ARObject:
    return ARObject(
        id="demo_current_001",
        type="current",
        category="surface_current",
        position=ARPosition(
            latitude=44.7000,
            longitude=37.8250,
        ),
        visual=ARVisual(
            icon="current_arrow",
            priority="medium",
        ),
        title="Поверхностное течение",
        source="Copernicus Marine (demo snapshot)",
        speed_m_s=0.21,
        direction_deg=137.0,
    )


def _demo_oil_forecast_object() -> ARObject:
    return ARObject(
        id="demo_oil_forecast_001",
        type="oil_forecast",
        category="oil_spill",
        position=ARPosition(
            latitude=44.7184,
            longitude=37.7957,
        ),
        visual=ARVisual(
            icon="oil_forecast",
            priority="high",
        ),
        title="Прогноз нефтяного загрязнения",
        source="OpenOil (demo result)",
        forecast_hours=6,
        particle_count=100,
        stranded_percent=100.0,
        terminal_state="stranded",
    )


def build_ar_scene(
    event_records: Iterable[dict],
    *,
    observer: ARPosition | None = None,
    heading_deg: float | None = None,
    max_distance_km: float | None = None,
) -> ARScene:
    """
    Build the conference AR scene.

    v0.4.1:
    - real canonical EventStore incidents;
    - cached/demo current and OpenOil forecast;
    - observer-relative distance/bearing;
    - HUD-ready distance label/tier;
    - optional snapshot heading -> relative angle / direction hint;
    - co-located objects are centered instead of assigned a fake direction;
    - optional distance filter.

    The AR request never starts OpenOil/OceanDrift/Copernicus jobs.
    """
    scene_observer = observer or ARPosition(
        latitude=DEFAULT_DEMO_LATITUDE,
        longitude=DEFAULT_DEMO_LONGITUDE,
    )

    raw_objects: list[ARObject] = []

    for record in event_records:
        ar_object = event_record_to_ar_object(record)

        if ar_object is not None:
            raw_objects.append(ar_object)

    raw_objects.extend([
        _demo_current_object(),
        _demo_oil_forecast_object(),
    ])

    objects = []

    for ar_object in raw_objects:
        with_metrics = _apply_observer_metrics(
            ar_object,
            scene_observer,
            heading_deg,
        )

        if (
            max_distance_km is not None
            and with_metrics.distance_m is not None
            and with_metrics.distance_m
            > max_distance_km * 1000.0
        ):
            continue

        objects.append(with_metrics)

    return ARScene(
        contract_version="0.4",
        scene_id="black_sea_conference_scene_v3",
        generated_at=_utc_now_iso(),
        center=ARPosition(
            latitude=DEFAULT_DEMO_LATITUDE,
            longitude=DEFAULT_DEMO_LONGITUDE,
        ),
        observer=scene_observer,
        heading_deg=heading_deg,
        objects=objects,
    )


def build_demo_ar_scene() -> ARScene:
    """
    Backward-compatible demo scene used by existing tests/tools.
    """
    demo_incident = ARObject(
        id="demo_incident_novorossiysk_001",
        type="incident",
        category="oil_spill",
        position=ARPosition(
            latitude=44.7240,
            longitude=37.7691,
        ),
        visual=ARVisual(
            icon="oil_spill",
            priority="critical",
        ),
        title="Экологический инцидент",
        source="demo",
        status="detected",
        confidence=0.95,
    )

    return ARScene(
        contract_version="0.4",
        scene_id="novorossiysk_conference_demo_v1",
        generated_at=_utc_now_iso(),
        center=ARPosition(
            latitude=DEFAULT_DEMO_LATITUDE,
            longitude=DEFAULT_DEMO_LONGITUDE,
        ),
        observer=ARPosition(
            latitude=DEFAULT_DEMO_LATITUDE,
            longitude=DEFAULT_DEMO_LONGITUDE,
        ),
        objects=[
            demo_incident,
            _demo_current_object(),
            _demo_oil_forecast_object(),
        ],
    )
