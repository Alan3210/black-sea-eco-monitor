from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.services.geos_cf_field import (
    build_cams_comparison_metadata,
    build_freshness,
    normalize_geos_cf_field,
)


def _field(product="pm25"):
    units = "µg/m³" if product == "pm25" else "mol/mol"
    return {
        "provider": "NASA GMAO",
        "model": "GEOS-CF v2",
        "product": product,
        "units": units,
        "run_time": "2026-09-19T09:00:00Z",
        "valid_time": "2026-09-19T09:30:00Z",
        "longitude": [26.0, 26.25],
        "latitude": [39.0, 39.25],
        "values": [[1.0, 2.0], [3.0, 4.0]],
    }


def test_freshness_reports_run_age_and_past_valid_time():
    now = datetime(2026, 9, 20, 12, 30, tzinfo=timezone.utc)
    result = build_freshness(_field(), now=now)

    assert result["run_age_hours"] == 27.5
    assert result["valid_time_offset_hours_from_now"] == -27.0
    assert result["valid_time_relation"] == "past"


def test_freshness_can_report_future_valid_time():
    field = _field()
    field["valid_time"] = "2026-09-20T18:30:00Z"
    now = datetime(2026, 9, 20, 12, 30, tzinfo=timezone.utc)

    result = build_freshness(field, now=now)
    assert result["valid_time_relation"] == "future"
    assert result["valid_time_offset_hours_from_now"] == 6.0


def test_pm25_is_unit_compatible_but_not_direct_compare_ready():
    result = build_cams_comparison_metadata("pm25")
    assert result["unit_compatible"] is True
    assert result["requires_unit_conversion"] is False
    assert result["direct_value_comparison_ready"] is False
    assert result["scientific_equivalence_assumed"] is False


def test_no2_requires_unit_conversion_before_cams_comparison():
    result = build_cams_comparison_metadata("no2")
    assert result["unit_compatible"] is False
    assert result["requires_unit_conversion"] is True
    assert result["direct_value_comparison_ready"] is False


def test_normalize_preserves_values_and_adds_metadata():
    now = datetime(2026, 9, 20, 12, 30, tzinfo=timezone.utc)
    field = _field()

    result = normalize_geos_cf_field(field, now=now)

    assert result["values"] == field["values"]
    assert result["freshness"]["run_age_hours"] == 27.5
    assert result["cams_comparison"]["unit_compatible"] is True


def test_rejects_non_ascending_longitude():
    field = _field()
    field["longitude"] = [26.25, 26.0]

    with pytest.raises(ValueError, match="longitude"):
        normalize_geos_cf_field(field)


def test_rejects_grid_shape_mismatch():
    field = _field()
    field["values"] = [[1.0], [2.0]]

    with pytest.raises(ValueError, match="column count"):
        normalize_geos_cf_field(field)
