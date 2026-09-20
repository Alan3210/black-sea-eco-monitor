from backend.api.air_field import router


def test_air_field_router_path():
    paths = {
        route.path
        for route in router.routes
    }

    assert "/air/field" in paths
