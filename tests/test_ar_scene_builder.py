from backend.services.ar_scene_builder import build_demo_ar_scene


def test_build_demo_ar_scene_has_expected_objects():
    scene = build_demo_ar_scene()

    assert scene.scene_id == "novorossiysk_conference_demo_v1"
    assert scene.center.latitude == 44.7240
    assert scene.center.longitude == 37.7691

    assert len(scene.objects) == 3

    object_types = {obj.type for obj in scene.objects}

    assert object_types == {
        "incident",
        "current",
        "oil_forecast",
    }


def test_demo_scene_is_json_serializable():
    scene = build_demo_ar_scene()

    data = scene.model_dump(mode="json")

    assert isinstance(data["objects"], list)
    assert data["objects"][0]["position"]["latitude"] == 44.7240
