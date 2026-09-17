from backend.schemas.ar import ARPosition
from backend.services.ar_scene_builder import (
    build_ar_scene,
    calculate_distance_and_bearing,
)


def _sample_event_record():
    return {
        "id": "evt_geo_test_001",
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


def test_same_position_has_zero_distance():
    point = ARPosition(
        latitude=44.724,
        longitude=37.7691,
    )

    distance_m, bearing_deg = calculate_distance_and_bearing(
        point,
        point,
    )

    assert distance_m == 0.0
    assert bearing_deg == 0.0


def test_eastward_target_has_eastward_bearing():
    observer = ARPosition(
        latitude=44.724,
        longitude=37.7691,
    )
    target = ARPosition(
        latitude=44.724,
        longitude=37.7791,
    )

    distance_m, bearing_deg = calculate_distance_and_bearing(
        observer,
        target,
    )

    assert 700.0 < distance_m < 900.0
    assert 80.0 < bearing_deg < 100.0


def test_scene_adds_distance_and_bearing():
    observer = ARPosition(
        latitude=44.724,
        longitude=37.7691,
    )

    scene = build_ar_scene(
        [_sample_event_record()],
        observer=observer,
    )

    incident = scene.objects[0]

    assert scene.observer == observer
    assert incident.distance_m == 0.0
    assert incident.bearing_deg == 0.0


def test_max_distance_filter_removes_far_objects():
    observer = ARPosition(
        latitude=44.724,
        longitude=37.7691,
    )

    scene = build_ar_scene(
        [_sample_event_record()],
        observer=observer,
        max_distance_km=1.0,
    )

    object_ids = {
        obj.id
        for obj in scene.objects
    }

    assert "evt_geo_test_001" in object_ids
    assert "demo_current_001" not in object_ids
    assert "demo_oil_forecast_001" not in object_ids
