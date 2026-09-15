from fastapi import FastAPI
from fastapi.testclient import (
    TestClient,
)

import backend.api.ocean_drift as api


def make_client():
    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app)


def test_ocean_drift_endpoint_returns_forecast(
    monkeypatch,
):
    monkeypatch.setattr(
        api,
        "run_surface_drift",
        lambda **kwargs: {
            "model": "OpenDrift OceanDrift",
            "seed": {
                "longitude": kwargs[
                    "longitude"
                ],
                "latitude": kwargs[
                    "latitude"
                ],
            },
            "horizons": [],
        },
    )

    response = make_client().get(
        "/ocean/drift/",
        params={
            "lon": 37.7691,
            "lat": 44.7240,
            "hours": 24,
            "particles": 100,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == (
        "OpenDrift OceanDrift"
    )


def test_ocean_drift_endpoint_maps_input_error_to_400(
    monkeypatch,
):
    from agents.ocean_data.drift_forecast import (
        OceanDriftInputError,
    )

    def fail(**kwargs):
        raise OceanDriftInputError(
            "bad request"
        )

    monkeypatch.setattr(
        api,
        "run_surface_drift",
        fail,
    )

    response = make_client().get(
        "/ocean/drift/",
        params={
            "lon": 37.7691,
            "lat": 44.7240,
        },
    )

    assert response.status_code == 400


def test_ocean_drift_endpoint_maps_runtime_error_to_503(
    monkeypatch,
):
    from agents.ocean_data.drift_forecast import (
        OceanDriftError,
    )

    def fail(**kwargs):
        raise OceanDriftError(
            "forcing unavailable"
        )

    monkeypatch.setattr(
        api,
        "run_surface_drift",
        fail,
    )

    response = make_client().get(
        "/ocean/drift/",
        params={
            "lon": 37.7691,
            "lat": 44.7240,
        },
    )

    assert response.status_code == 503
