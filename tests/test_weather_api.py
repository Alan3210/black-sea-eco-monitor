from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.weather import (
    get_weather_provider,
    router,
)
from backend.schemas.weather import (
    WeatherPoint,
    WeatherProvenance,
)
from backend.services.ecmwf_weather_provider import (
    WeatherSourceUnavailable,
    WeatherTimeUnavailable,
)


class FakeWeatherProvider:
    provider_name = "fake"

    def __init__(self):
        self.calls = []

    def get_point(
        self,
        *,
        latitude,
        longitude,
        valid_time=None,
    ):
        self.calls.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "valid_time": valid_time,
            }
        )

        actual_valid_time = (
            valid_time
            if valid_time is not None
            else datetime(
                2026,
                9,
                19,
                9,
                tzinfo=timezone.utc,
            )
        )

        return WeatherPoint(
            latitude=latitude,
            longitude=longitude,
            wind_u_10m_ms=-2.0,
            wind_v_10m_ms=-3.0,
            wind_speed_10m_ms=3.605551275463989,
            wind_from_direction_deg=33.690067525979785,
            precipitation_rate_mm_h=0.2,
            precipitation_accumulation_mm=1.8,
            precipitation_interval_start=datetime(
                2026,
                9,
                19,
                6,
                tzinfo=timezone.utc,
            ),
            precipitation_interval_end=actual_valid_time,
            provenance=WeatherProvenance(
                provider="ecmwf",
                model="ifs",
                product="open-data-0p25",
                data_kind="forecast",
                forecast_reference_time=datetime(
                    2026,
                    9,
                    19,
                    0,
                    tzinfo=timezone.utc,
                ),
                valid_time=actual_valid_time,
                retrieved_at=datetime(
                    2026,
                    9,
                    19,
                    7,
                    tzinfo=timezone.utc,
                ),
                source_uri="google",
                fallback_used=False,
            ),
        )


def make_client(provider):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[
        get_weather_provider
    ] = lambda: provider
    return TestClient(app)


def test_weather_point_endpoint_returns_canonical_contract():
    provider = FakeWeatherProvider()
    client = make_client(provider)

    response = client.get(
        "/weather/point",
        params={
            "latitude": 44.6,
            "longitude": 37.8,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["latitude"] == 44.6
    assert data["longitude"] == 37.8
    assert data["wind_u_10m_ms"] == -2.0
    assert data["wind_v_10m_ms"] == -3.0
    assert data["provenance"]["provider"] == "ecmwf"
    assert data["provenance"]["model"] == "ifs"
    assert data["units"]["wind_speed"] == "m/s"

    assert provider.calls == [
        {
            "latitude": 44.6,
            "longitude": 37.8,
            "valid_time": None,
        }
    ]


def test_weather_point_endpoint_passes_valid_time():
    provider = FakeWeatherProvider()
    client = make_client(provider)

    response = client.get(
        "/weather/point",
        params={
            "latitude": 44.6,
            "longitude": 37.8,
            "valid_time": "2026-09-19T12:00:00Z",
        },
    )

    assert response.status_code == 200

    call = provider.calls[0]
    assert call["valid_time"] == datetime(
        2026,
        9,
        19,
        12,
        tzinfo=timezone.utc,
    )


def test_weather_point_endpoint_rejects_invalid_coordinates():
    provider = FakeWeatherProvider()
    client = make_client(provider)

    response = client.get(
        "/weather/point",
        params={
            "latitude": 100.0,
            "longitude": 37.8,
        },
    )

    assert response.status_code == 422
    assert provider.calls == []


def test_weather_point_endpoint_maps_time_error_to_422():
    class Provider(FakeWeatherProvider):
        def get_point(self, **kwargs):
            raise WeatherTimeUnavailable(
                "requested valid time is outside forecast horizon"
            )

    client = make_client(Provider())

    response = client.get(
        "/weather/point",
        params={
            "latitude": 44.6,
            "longitude": 37.8,
        },
    )

    assert response.status_code == 422
    assert (
        "outside forecast horizon"
        in response.json()["detail"]
    )


def test_weather_point_endpoint_maps_source_error_to_503():
    class Provider(FakeWeatherProvider):
        def get_point(self, **kwargs):
            raise WeatherSourceUnavailable(
                "all ECMWF mirrors failed"
            )

    client = make_client(Provider())

    response = client.get(
        "/weather/point",
        params={
            "latitude": 44.6,
            "longitude": 37.8,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "all ECMWF mirrors failed"
