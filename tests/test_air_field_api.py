from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.api.air_field as api_module


class FakeService:
    def get_field(
        self,
        **kwargs,
    ):
        return {
            "provider":
                "Copernicus Atmosphere Monitoring Service",
            "dataset":
                "cams-europe-air-quality-forecasts",
            "model":
                "ensemble",
            "semantics": {
                "kind":
                    "model_forecast",
                "observation":
                    False,
            },
            "pollutant": {
                "id":
                    kwargs["pollutant"],
                "units":
                    "µg/m3",
            },
            "lead_hour":
                kwargs["lead_hour"],
            "grid": {
                "shape":
                    [1, 1],
                "values":
                    [[1.0]],
            },
        }


def test_air_field_api_contract(
    monkeypatch,
):
    monkeypatch.setattr(
        api_module,
        "get_air_field_service",
        lambda: FakeService(),
    )

    app = FastAPI()
    app.include_router(
        api_module.router
    )

    client = TestClient(
        app
    )

    response = client.get(
        "/air/field",
        params={
            "pollutant":
                "pm25",
            "run_date":
                "2026-09-19",
            "lead_hour":
                6,
            "stride":
                2,
        },
    )

    assert (
        response.status_code
        == 200
    )

    payload = response.json()

    assert payload[
        "pollutant"
    ]["id"] == "pm25"

    assert payload[
        "semantics"
    ]["kind"] == (
        "model_forecast"
    )
