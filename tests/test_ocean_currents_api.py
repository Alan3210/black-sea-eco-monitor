from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.api.ocean_currents as ocean_api


def make_app():
    app = FastAPI()
    app.include_router(
        ocean_api.router
    )
    return app


def test_ocean_currents_api_returns_provider_payload(
    monkeypatch,
):
    def fake_provider(**kwargs):
        return {
            "dataset_id": "test",
            "vector_count": 1,
            "vectors": [
                {
                    "latitude": 44.0,
                    "longitude": 35.0,
                    "u": 0.1,
                    "v": 0.2,
                    "speed": 0.2236,
                    "direction_deg": 26.57,
                }
            ],
        }

    monkeypatch.setattr(
        ocean_api,
        "get_surface_currents",
        fake_provider,
    )

    client = TestClient(
        make_app()
    )

    response = client.get(
        "/ocean/currents/?stride=8"
    )

    assert response.status_code == 200
    assert response.json()["vector_count"] == 1


def test_ocean_currents_api_validates_stride():
    client = TestClient(
        make_app()
    )

    response = client.get(
        "/ocean/currents/?stride=0"
    )

    assert response.status_code == 422
