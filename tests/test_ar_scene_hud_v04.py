from backend.schemas.ar import ARPosition
from backend.services.ar_scene_builder import (
    build_ar_scene,
    calculate_relative_angle,
    direction_hint,
    distance_label,
    distance_tier,
)


def _sample_event_record():
    return {
        "id": "evt_v04_001",
        "category": "industrial_fire",
        "location": {
            "name": "Novorossiysk",
            "latitude": 44.724,
            "longitude": 37.7691,
            "type": "city",
            "confidence": 0.9,
            "source": "canonical_database",
        },
        "time": {
            "incident_time": None,
            "detection_time": "2026-09-12T22:27:14+00:00",
            "source_time": "2026-09-09T03:24:19+00:00",
        },
        "primary_title": "Test industrial fire",
        "status": "detected",
        "severity": "medium",
        "confidence": 0.8,
        "evidence_count": 3,
    }


def test_relative_angle_right():
    assert calculate_relative_angle(
        bearing_deg=75.0,
        heading_deg=40.0,
    ) == 35.0


def test_relative_angle_wraps_left():
    assert calculate_relative_angle(
        bearing_deg=350.0,
        heading_deg=10.0,
    ) == -20.0


def test_direction_hint():
    assert direction_hint(-25.0) == "left"
    assert direction_hint(0.0) == "center"
    assert direction_hint(25.0) == "right"


def test_distance_label():
    assert distance_label(850.0) == "850 m"
    assert distance_label(2_700.0) == "2.7 km"
    assert distance_label(24_400.0) == "24 km"


def test_distance_tier():
    assert distance_tier(500.0) == "near"
    assert distance_tier(5_000.0) == "medium"
    assert distance_tier(25_000.0) == "far"


def test_scene_adds_hud_fields():
    observer = ARPosition(
        latitude=44.724,
        longitude=37.7691,
    )

    scene = build_ar_scene(
        [_sample_event_record()],
        observer=observer,
        heading_deg=0.0,
    )

    incident = scene.objects[0]

    assert scene.contract_version == "0.4"
    assert scene.heading_deg == 0.0
    assert incident.distance_label == "0 m"
    assert incident.distance_tier == "near"
    assert incident.relative_angle_deg == 0.0
    assert incident.direction_hint == "center"


def test_colocated_object_stays_centered_for_nonzero_heading():
    observer = ARPosition(
        latitude=44.724,
        longitude=37.7691,
    )

    scene = build_ar_scene(
        [_sample_event_record()],
        observer=observer,
        heading_deg=40.0,
    )

    incident = scene.objects[0]

    assert incident.distance_m == 0.0
    assert incident.relative_angle_deg == 0.0
    assert incident.direction_hint == "center"
