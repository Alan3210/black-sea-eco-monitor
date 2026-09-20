from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.services.air_model_crosscheck import (
    AirModelCrosscheckUnavailable,
    build_model_crosscheck,
    nearest_cams_target,
)


def _cams_field():
    return {
        "provider": "Copernicus",
        "dataset": "cams-europe-air-quality-forecasts",
        "model": "ensemble",
        "units": "µg/m³",
        "run_time": "2026-09-19T00:00:00Z",
        "valid_time": "2026-09-19T10:00:00Z",
        "lead_hour": 10,
        "longitude": [26.0, 26.1, 26.2, 26.3],
        "latitude": [39.0, 39.1, 39.2, 39.3],
        "values": [
            [10.0, 12.0, 14.0, 16.0],
            [12.0, 14.0, 16.0, 18.0],
            [14.0, 16.0, 18.0, 20.0],
            [16.0, 18.0, 20.0, 22.0],
        ],
        "provenance": {"test": True},
    }


def _geos_field():
    return {
        "provider": "NASA GMAO",
        "dataset": "geos-cf-v2",
        "model": "GEOS-CF v2",
        "product": "pm25",
        "units": "µg/m³",
        "run_time": "2026-09-19T09:00:00Z",
        "valid_time": "2026-09-19T09:30:00Z",
        "forecast_time_index": 0,
        "longitude": [26.05, 26.15, 26.25],
        "latitude": [39.05, 39.15, 39.25],
        "values": [
            [12.0, 15.0, 18.0],
            [15.0, 18.0, 21.0],
            [18.0, 21.0, 24.0],
        ],
        "freshness": {"valid_time_relation": "past"},
        "provenance": {"test": True},
    }


def test_nearest_cams_target_rounds_half_hour_forward():
    target = nearest_cams_target("2026-09-19T09:30:00Z")
    assert target["run_date"].isoformat() == "2026-09-19"
    assert target["lead_hour"] == 10
    assert target["target_valid_time"].isoformat() == (
        "2026-09-19T10:00:00+00:00"
    )
    assert target["delta_minutes_to_geos"] == 30.0


def test_nearest_cams_target_rolls_midnight():
    target = nearest_cams_target("2026-09-19T23:40:00Z")
    assert target["run_date"].isoformat() == "2026-09-20"
    assert target["lead_hour"] == 0


def test_build_crosscheck_aligns_time_and_grid():
    result = build_model_crosscheck(
        cams_field=_cams_field(),
        geos_field=_geos_field(),
        max_time_gap_minutes=45.0,
    )

    assert result["time_alignment"]["absolute_gap_minutes"] == 30.0
    assert result["time_alignment"]["status"] == "aligned"
    assert result["spatial_alignment"]["reference_grid"] == "GEOS-CF v2"
    assert result["spatial_alignment"]["compared_points"] > 0
    assert result["metrics"]["count"] > 0


def test_crosscheck_metrics_have_explicit_bias_direction():
    result = build_model_crosscheck(
        cams_field=_cams_field(),
        geos_field=_geos_field(),
    )

    assert "bias_geos_minus_cams" in result["metrics"]
    assert "mae" in result["metrics"]
    assert "median_absolute_difference" in result["metrics"]
    assert "rmse" in result["metrics"]
    assert "pearson_r" in result["metrics"]


def test_crosscheck_does_not_claim_agreement_classification():
    result = build_model_crosscheck(
        cams_field=_cams_field(),
        geos_field=_geos_field(),
    )

    assert (
        result["semantics"]["agreement_classification"]
        == "not_calibrated"
    )


def test_time_gap_over_limit_is_rejected():
    cams = _cams_field()
    cams["valid_time"] = "2026-09-19T12:00:00Z"

    with pytest.raises(
        AirModelCrosscheckUnavailable,
        match="valid times exceed",
    ):
        build_model_crosscheck(
            cams_field=cams,
            geos_field=_geos_field(),
            max_time_gap_minutes=45.0,
        )


def test_unit_mismatch_is_rejected():
    cams = _cams_field()
    cams["units"] = "mg/m³"

    with pytest.raises(Exception, match="Unit mismatch"):
        build_model_crosscheck(
            cams_field=cams,
            geos_field=_geos_field(),
        )


def test_gas_product_not_supported_in_1_5c():
    geos = _geos_field()
    geos["product"] = "no2"
    geos["units"] = "mol/mol"

    with pytest.raises(ValueError, match="pm25 and pm10"):
        build_model_crosscheck(
            cams_field=_cams_field(),
            geos_field=geos,
        )
