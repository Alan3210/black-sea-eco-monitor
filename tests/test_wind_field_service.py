from datetime import datetime, timezone

import numpy as np
import pytest
import xarray as xr

from backend.services.wind_field import (
    EcmwfWindFieldService,
    normalize_wind_field_time,
    validate_wind_field_stride,
    wind_direction_from_deg,
    wind_direction_to_deg,
)


def test_north_wind_moves_south():
    assert wind_direction_from_deg(
        0.0,
        -5.0,
    ) == pytest.approx(0.0)
    assert wind_direction_to_deg(
        0.0,
        -5.0,
    ) == pytest.approx(180.0)


def test_westerly_wind_moves_east():
    assert wind_direction_from_deg(
        5.0,
        0.0,
    ) == pytest.approx(270.0)
    assert wind_direction_to_deg(
        5.0,
        0.0,
    ) == pytest.approx(90.0)


def test_normalize_time_accepts_z():
    assert normalize_wind_field_time(
        "2026-09-19T08:30:00Z"
    ) == datetime(
        2026,
        9,
        19,
        8,
        30,
        tzinfo=timezone.utc,
    )


def test_stride_validation():
    assert validate_wind_field_stride(2) == 2

    with pytest.raises(ValueError):
        validate_wind_field_stride(0)

    with pytest.raises(ValueError):
        validate_wind_field_stride(9)


class FakeForcing:
    def __init__(self):
        times = np.array(
            [
                np.datetime64(
                    "2026-09-19T06:00:00"
                ),
                np.datetime64(
                    "2026-09-19T09:00:00"
                ),
                np.datetime64(
                    "2026-09-19T12:00:00"
                ),
            ]
        )
        latitude = np.array(
            [44.0, 45.0, 46.0],
        )
        longitude = np.array(
            [36.0, 37.0, 38.0],
        )

        u = np.zeros(
            (3, 3, 3),
            dtype=float,
        )
        v = np.zeros(
            (3, 3, 3),
            dtype=float,
        )

        u[0, :, :] = 2.0
        u[1, :, :] = 4.0
        u[2, :, :] = 6.0

        v[0, :, :] = -3.0
        v[1, :, :] = -5.0
        v[2, :, :] = -7.0

        self.dataset = xr.Dataset(
            {
                "u10": (
                    (
                        "time",
                        "latitude",
                        "longitude",
                    ),
                    u,
                ),
                "v10": (
                    (
                        "time",
                        "latitude",
                        "longitude",
                    ),
                    v,
                ),
            },
            coords={
                "time": times,
                "latitude": latitude,
                "longitude": longitude,
            },
        )
        self.steps = (6, 9, 12)

    def provenance(self):
        return {
            "product": "open-data-0p25",
            "forecast_reference_time": (
                "2026-09-19T00:00:00+00:00"
            ),
            "retrieved_at": (
                "2026-09-19T07:00:00+00:00"
            ),
            "sources": ["google"],
            "fallback_used": False,
        }


class FakeBuilder:
    def __init__(self):
        self.calls = []

    def build(
        self,
        *,
        start_time,
        hours,
        bbox,
    ):
        self.calls.append(
            {
                "start_time": start_time,
                "hours": hours,
                "bbox": bbox,
            }
        )
        return FakeForcing()


def test_service_interpolates_and_decimates():
    builder = FakeBuilder()
    service = EcmwfWindFieldService(
        builder=builder
    )

    payload = service.get_field(
        at="2026-09-19T07:30:00Z",
        stride=2,
        bbox={
            "west": 36.0,
            "south": 44.0,
            "east": 38.0,
            "north": 46.0,
        },
    )

    assert builder.calls[0]["hours"] == 1
    assert payload["vector_count"] == 4
    assert payload["sources"] == ["google"]

    vector = payload["vectors"][0]

    assert vector["u_ms"] == pytest.approx(
        3.0
    )
    assert vector["v_ms"] == pytest.approx(
        -4.0
    )
    assert vector["speed_ms"] == pytest.approx(
        5.0
    )
    assert vector[
        "direction_from_deg"
    ] == pytest.approx(
        323.13,
        abs=0.01,
    )
    assert vector[
        "direction_to_deg"
    ] == pytest.approx(
        143.13,
        abs=0.01,
    )


def test_service_reports_speed_stats():
    service = EcmwfWindFieldService(
        builder=FakeBuilder()
    )

    payload = service.get_field(
        at="2026-09-19T07:30:00Z",
        stride=1,
        bbox={
            "west": 36.0,
            "south": 44.0,
            "east": 38.0,
            "north": 46.0,
        },
    )

    assert payload["speed_stats"] == {
        "min_speed_ms": 5.0,
        "mean_speed_ms": 5.0,
        "max_speed_ms": 5.0,
    }
