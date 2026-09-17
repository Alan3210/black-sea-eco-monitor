from backend.services.ar_scene_builder import (
    build_ar_scene,
    event_record_to_ar_object,
)


def _sample_event_record():
    return {
        "id": "evt_test_001",
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


def test_event_record_maps_to_ar_incident():
    result = event_record_to_ar_object(
        _sample_event_record()
    )

    assert result is not None
    assert result.id == "evt_test_001"
    assert result.type == "incident"
    assert result.category == "industrial_fire"
    assert result.position.latitude == 44.724
    assert result.position.longitude == 37.7691
    assert result.visual.icon == "industrial_fire"
    assert result.visual.priority == "medium"
    assert result.location_name == "Novorossiysk"
    assert result.location_type == "city"
    assert result.location_confidence == 0.9
    assert result.coordinate_source == "canonical_database"
    assert result.detection_time == "2026-09-12T22:27:14+00:00"
    assert result.source_time == "2026-09-09T03:24:19+00:00"
    assert result.evidence_count == 3


def test_event_without_coordinates_is_skipped():
    record = _sample_event_record()
    record["location"]["latitude"] = None

    result = event_record_to_ar_object(record)

    assert result is None


def test_scene_contains_real_incident_plus_cached_environment():
    scene = build_ar_scene([
        _sample_event_record()
    ])

    assert scene.scene_id == "black_sea_conference_scene_v3"
    assert len(scene.objects) == 3

    assert scene.objects[0].id == "evt_test_001"

    object_types = {
        obj.type
        for obj in scene.objects
    }

    assert object_types == {
        "incident",
        "current",
        "oil_forecast",
    }
