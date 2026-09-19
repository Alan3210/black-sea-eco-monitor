from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.wind_field import (
    get_wind_field_service,
    router,
)


class FakeService:
    def get_field(
        self,
        *,
        at=None,
        stride=2,
        bbox=None,
    ):
        return {
            "provider": "ecmwf",
            "model": "ifs",
            "height_m": 10,
            "requested_time": (
                at
                or "2026-09-19T08:00:00+00:00"
            ),
            "valid_time": (
                at
                or "2026-09-19T08:00:00+00:00"
            ),
            "forecast_reference_time": (
                "2026-09-19T00:00:00+00:00"
            ),
            "retrieved_at": (
                "2026-09-19T07:00:00+00:00"
            ),
            "sources": ["google"],
            "fallback_used": False,
            "temporal_interpolation": (
                "linear_between_native_ifs_steps"
            ),
            "direction_convention": {},
            "bbox": {},
            "stride": stride,
            "native_grid_shape": {
                "latitude": 30,
                "longitude": 61,
            },
            "vector_count": 1,
            "speed_stats": {
                "min_speed_ms": 4.0,
                "mean_speed_ms": 4.0,
                "max_speed_ms": 4.0,
            },
            "vectors": [
                {
                    "latitude": 44.6,
                    "longitude": 37.8,
                    "u_ms": -2.0,
                    "v_ms": -3.464102,
                    "speed_ms": 4.0,
                    "direction_from_deg": 30.0,
                    "direction_to_deg": 210.0,
                }
            ],
            "forcing_steps": [6, 9, 12],
            "forcing_cube_start": (
                "2026-09-19T06:00:00+00:00"
            ),
            "forcing_cube_end": (
                "2026-09-19T12:00:00+00:00"
            ),
        }


def make_client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[
        get_wind_field_service
    ] = lambda: FakeService()
    return TestClient(app)


def test_wind_field_api_contract():
    client = make_client()

    response = client.get(
        "/weather/wind-field",
        params={
            "at": "2026-09-19T08:00:00Z",
            "stride": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["provider"] == "ecmwf"
    assert payload["model"] == "ifs"
    assert payload["height_m"] == 10
    assert payload["stride"] == 2
    assert payload["vector_count"] == 1
    assert payload["vectors"][0][
        "direction_from_deg"
    ] == 30.0
    assert payload["vectors"][0][
        "direction_to_deg"
    ] == 210.0


def test_wind_field_api_rejects_bad_stride():
    client = make_client()

    response = client.get(
        "/weather/wind-field",
        params={
            "stride": 0,
        },
    )

    assert response.status_code == 422
