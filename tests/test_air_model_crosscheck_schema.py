from __future__ import annotations

import pytest

from backend.services.air_model_crosscheck import (
    _extract_units,
    _field_arrays,
    _normalize_unit_text,
    build_model_crosscheck,
)


def _cams_nested():
    return {
        "provider": "Copernicus Atmosphere Monitoring Service",
        "dataset": "cams-europe-air-quality-forecasts",
        "model": "ensemble",
        "pollutant": {
            "id": "pm25",
            "label": "PM2.5",
            "units": "µg/m3",
            "quality_status": "validated",
            "source_variable": "pm2p5_conc",
        },
        "run_time": "2026-09-19T00:00:00+00:00",
        "valid_time": "2026-09-19T10:00:00+00:00",
        "lead_hour": 10,
        "grid": {
            "longitude": [26.0, 26.1, 26.2],
            "latitude": [39.0, 39.1, 39.2],
            "values": [
                [10.0, 11.0, 12.0],
                [12.0, 13.0, 14.0],
                [14.0, 15.0, 16.0],
            ],
        },
    }


def _geos():
    return {
        "provider": "NASA GMAO",
        "model": "GEOS-CF v2",
        "product": "pm25",
        "units": "µg/m³",
        "run_time": "2026-09-19T09:00:00Z",
        "valid_time": "2026-09-19T09:30:00Z",
        "longitude": [26.05, 26.15],
        "latitude": [39.05, 39.15],
        "values": [
            [12.0, 14.0],
            [14.0, 16.0],
        ],
    }


def test_extract_units_from_nested_cams_pollutant():
    assert _extract_units(_cams_nested()) == "µg/m3"


def test_normalizes_m3_and_superscript_m3_as_same_unit():
    assert _normalize_unit_text("µg/m3") == "ug/m3"
    assert _normalize_unit_text("µg/m³") == "ug/m3"


def test_field_arrays_accept_nested_cams_grid():
    lon, lat, values = _field_arrays(_cams_nested())
    assert lon.tolist() == [26.0, 26.1, 26.2]
    assert lat.tolist() == [39.0, 39.1, 39.2]
    assert values.shape == (3, 3)


def test_crosscheck_accepts_real_cams_canonical_shape():
    result = build_model_crosscheck(
        cams_field=_cams_nested(),
        geos_field=_geos(),
    )

    assert result["unit_alignment"]["status"] == "compatible"
    assert result["unit_alignment"]["cams_raw"] == "µg/m3"
    assert result["unit_alignment"]["geos_cf_raw"] == "µg/m³"
    assert result["spatial_alignment"]["compared_points"] == 4
    assert result["metrics"]["count"] == 4
    assert (
        result["sources"]["cams"]["source_variable"]
        == "pm2p5_conc"
    )


def test_real_cams_schema_does_not_require_top_level_units():
    cams = _cams_nested()
    assert "units" not in cams
    assert "longitude" not in cams
    assert "latitude" not in cams
    assert "values" not in cams

    result = build_model_crosscheck(
        cams_field=cams,
        geos_field=_geos(),
    )
    assert result["metrics"]["count"] > 0
