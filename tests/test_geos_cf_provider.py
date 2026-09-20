from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.services.geos_cf_provider import (
    DEFAULT_BLACK_SEA_BBOX,
    GeosCFProvider,
    _bbox_to_indices,
    geos_cf_semantics,
    parse_grads_min,
    product_info,
)


class FakeArray:
    def __init__(self, data, attributes=None):
        self._data = np.asarray(data)
        self.attributes = attributes or {}

    def __getitem__(self, item):
        return FakeArray(self._data[item], self.attributes)

    @property
    def data(self):
        return self._data


class FakeDataset:
    def __init__(self):
        lon = np.arange(-180.0, 180.0, 0.25)
        lat = np.arange(-90.0, 90.0001, 0.25)

        field = np.zeros((120, 1, len(lat), len(lon)), dtype=np.float32)

        lon_start, lon_end, lat_start, lat_end = _bbox_to_indices(
            DEFAULT_BLACK_SEA_BBOX
        )

        local = np.arange(
            (lat_end - lat_start + 1) * (lon_end - lon_start + 1),
            dtype=np.float32,
        ).reshape(
            lat_end - lat_start + 1,
            lon_end - lon_start + 1,
        )
        field[0, 0, lat_start:lat_end + 1, lon_start:lon_end + 1] = local

        self.variables = {
            "time": FakeArray(
                np.arange(120),
                attributes={
                    "grads_min": "09:30z19sep2026",
                    "grads_step": "60mn",
                },
            ),
            "lon": FakeArray(lon),
            "lat": FakeArray(lat),
            "pm25_rh35": FakeArray(field),
        }

    def __getitem__(self, key):
        return self.variables[key]


def test_black_sea_bbox_indices_match_native_quarter_degree_grid():
    assert _bbox_to_indices(DEFAULT_BLACK_SEA_BBOX) == (
        824,
        894,
        516,
        552,
    )


def test_parses_geos_grads_time():
    dt = parse_grads_min("09:30z19sep2026")
    assert dt.isoformat() == "2026-09-19T09:30:00+00:00"


def test_pm25_semantics_are_forecast_not_observation():
    semantics = geos_cf_semantics("pm25")
    assert semantics["kind"] == "model_forecast"
    assert semantics["model_forecast"] is True
    assert semantics["observation"] is False
    assert semantics["station_measurement"] is False
    assert semantics["satellite_observation"] is False
    assert semantics["surface_field"] is True
    assert semantics["direct_cams_unit_comparison"] is True


def test_gas_native_units_are_not_direct_cams_mass_units():
    info = product_info("no2")
    assert info["units"] == "mol/mol"
    assert info["direct_cams_unit_comparison"] is False


def test_fetches_black_sea_pm25_field_and_times(tmp_path):
    provider = GeosCFProvider(
        cache_dir=tmp_path,
        opener=lambda _: FakeDataset(),
    )

    field = provider.fetch_field(
        product="pm25",
        time_index=0,
        stride=1,
    )

    assert field["provider"] == "NASA GMAO"
    assert field["model"] == "GEOS-CF v2"
    assert field["source_variable"] == "pm25_rh35"
    assert field["units"] == "µg/m³"
    assert field["grid"]["width"] == 71
    assert field["grid"]["height"] == 37
    assert field["run_time"] == "2026-09-19T09:00:00Z"
    assert field["first_valid_time"] == "2026-09-19T09:30:00Z"
    assert field["valid_time"] == "2026-09-19T09:30:00Z"
    assert field["lead_hours_from_nominal_run"] == 0.5
    assert field["statistics"]["count"] == 37 * 71


def test_stride_subsamples_without_interpolation(tmp_path):
    provider = GeosCFProvider(
        cache_dir=tmp_path,
        opener=lambda _: FakeDataset(),
    )
    field = provider.fetch_field(
        product="pm25",
        time_index=0,
        stride=2,
    )

    assert field["grid"]["stride"] == 2
    assert field["grid"]["width"] == 36
    assert field["grid"]["height"] == 19


def test_cache_is_run_scoped_and_second_call_hits_cache(tmp_path):
    provider = GeosCFProvider(
        cache_dir=tmp_path,
        opener=lambda _: FakeDataset(),
    )

    first = provider.fetch_field(product="pm25")
    second = provider.fetch_field(product="pm25")

    assert first["provenance"]["cache_hit"] is False
    assert second["provenance"]["cache_hit"] is True
    assert second["run_time"] == first["run_time"]
    assert Path(second["provenance"]["cache_path"]).exists()


def test_rejects_invalid_time_index(tmp_path):
    provider = GeosCFProvider(
        cache_dir=tmp_path,
        opener=lambda _: FakeDataset(),
    )
    with pytest.raises(ValueError, match="time_index"):
        provider.fetch_field(
            product="pm25",
            time_index=120,
        )


def test_supported_products():
    assert set(
        ["pm25", "pm10", "no2", "so2", "o3", "co"]
    ).issubset(
        {"pm25", "pm10", "no2", "so2", "o3", "co"}
    )
