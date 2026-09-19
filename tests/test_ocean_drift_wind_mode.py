import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.ocean_data.drift_forecast import (
    DEFAULT_FORCING_MODE,
    DEFAULT_WIND_DRIFT_FACTOR,
    FORCING_MODE_CURRENT_ONLY,
    FORCING_MODE_CURRENTS_PLUS_WIND,
    OceanDriftInputError,
    _cache_key,
    drift_scope,
    normalize_forcing_mode,
    wind_drift_factor_for_mode,
)
import backend.api.ocean_drift as drift_api


def test_default_mode_remains_current_only():
    assert DEFAULT_FORCING_MODE == "current_only"
    assert normalize_forcing_mode(None) == FORCING_MODE_CURRENT_ONLY


def test_currents_plus_wind_mode_is_supported():
    assert (
        normalize_forcing_mode("currents_plus_wind")
        == FORCING_MODE_CURRENTS_PLUS_WIND
    )
    assert (
        drift_scope(FORCING_MODE_CURRENTS_PLUS_WIND)
        == "passive_surface_tracer_currents_plus_direct_windage"
    )
    assert (
        wind_drift_factor_for_mode(
            FORCING_MODE_CURRENTS_PLUS_WIND
        )
        == pytest.approx(DEFAULT_WIND_DRIFT_FACTOR)
    )


def test_current_only_has_zero_direct_windage():
    assert (
        wind_drift_factor_for_mode(FORCING_MODE_CURRENT_ONLY)
        == 0.0
    )


def test_unknown_mode_is_rejected():
    with pytest.raises(OceanDriftInputError):
        normalize_forcing_mode("oil_magic")


def test_cache_key_separates_forcing_modes():
    common = dict(
        start_time=__import__("datetime").datetime(
            2026, 9, 19, 9, 0, 0
        ),
        longitude=37.8,
        latitude=44.6,
        hours=6,
        particles=100,
        radius_m=500.0,
        diffusivity_m2_s=2.0,
    )

    current_key = _cache_key(
        **common,
        forcing_mode=FORCING_MODE_CURRENT_ONLY,
    )
    wind_key = _cache_key(
        **common,
        forcing_mode=FORCING_MODE_CURRENTS_PLUS_WIND,
    )

    assert current_key != wind_key


def test_api_passes_explicit_forcing_mode(monkeypatch):
    calls = []

    def fake_run_surface_drift(**kwargs):
        calls.append(kwargs)
        return {
            "scope": drift_scope(kwargs["forcing_mode"]),
            "horizons": [],
        }

    monkeypatch.setattr(
        drift_api,
        "run_surface_drift",
        fake_run_surface_drift,
    )

    app = FastAPI()
    app.include_router(drift_api.router)
    client = TestClient(app)

    response = client.get(
        "/ocean/drift/",
        params={
            "lon": 37.8,
            "lat": 44.6,
            "hours": 6,
            "particles": 100,
            "forcing_mode": "currents_plus_wind",
        },
    )

    assert response.status_code == 200
    assert calls[0]["forcing_mode"] == "currents_plus_wind"
    assert (
        response.json()["scope"]
        == "passive_surface_tracer_currents_plus_direct_windage"
    )
