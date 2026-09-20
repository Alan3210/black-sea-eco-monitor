from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from backend.services.sentinel5p_satellite_field import (
    Sentinel5PNoCoverageError,
    _day_window,
    fetch_latest_available_satellite_field,
    read_satellite_field,
)


def _write_fixture(
    tmp_path: Path,
    *,
    name: str = "fixture",
    valid: bool = True,
) -> tuple[Path, Path]:
    tif = tmp_path / f"{name}.tif"
    metadata = tmp_path / f"{name}.json"

    values = np.array(
        [
            [1.0, 2.0, np.nan, 4.0],
            [5.0, -1.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
        ],
        dtype=np.float32,
    )
    mask = np.array(
        [
            [1.0, 1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0, 0.0],
            [1.0, 1.0, 1.0, 1.0],
        ],
        dtype=np.float32,
    )
    if not valid:
        mask[:] = 0.0
        values[:] = np.nan

    with rasterio.open(
        tif,
        "w",
        driver="GTiff",
        width=4,
        height=3,
        count=2,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(26.0, 48.0, 0.05, 0.05),
    ) as ds:
        ds.write(values, 1)
        ds.write(mask, 2)

    metadata.write_text(
        json.dumps(
            {
                "provider": "test-provider",
                "collection": "sentinel-5p-l2",
                "platform": "Sentinel-5P",
                "instrument": "TROPOMI",
                "product": "no2",
                "band": "NO2",
                "quantity": "nitrogen_dioxide_tropospheric_column",
                "units": "mol/m^2",
                "time_from": "2026-09-20T00:00:00Z",
                "time_to": "2026-09-20T23:59:59Z",
                "timeliness": "NRTI",
                "min_qa": 75,
                "upsampling": "NEAREST",
                "sha256": name,
                "fetched_at": "2026-09-20T09:00:00Z",
                "sample_type": "FLOAT32",
                "bands": ["NO2", "dataMask"],
            }
        ),
        encoding="utf-8",
    )
    return tif, metadata


class FakeProvider:
    def __init__(self, by_day: dict[str, tuple[Path, Path]]):
        self.by_day = by_day
        self.calls: list[str] = []

    def fetch_geotiff(self, **kwargs):
        day = kwargs["start"].date().isoformat()
        self.calls.append(day)
        tif, metadata = self.by_day[day]
        return SimpleNamespace(
            path=tif,
            metadata_path=metadata,
            cache_hit=True,
        )


def test_latitude_is_ascending_and_pixel_centred(tmp_path):
    tif, metadata = _write_fixture(tmp_path)
    result = read_satellite_field(
        geotiff_path=tif,
        metadata_path=metadata,
        product="no2",
    )

    assert result["latitude"] == pytest.approx(
        [47.875, 47.925, 47.975]
    )
    assert result["longitude"] == pytest.approx(
        [26.025, 26.075, 26.125, 26.175]
    )
    assert result["grid"]["latitude_order"] == "ascending"


def test_values_flip_with_latitude_and_mask_to_null(tmp_path):
    tif, metadata = _write_fixture(tmp_path)
    result = read_satellite_field(
        geotiff_path=tif,
        metadata_path=metadata,
        product="no2",
    )

    assert result["values"][0] == [9.0, 10.0, 11.0, 12.0]
    assert result["values"][1][1] == -1.0
    assert result["values"][1][3] is None
    assert result["values"][2][2] is None


def test_statistics_use_full_valid_source_grid(tmp_path):
    tif, metadata = _write_fixture(tmp_path)
    result = read_satellite_field(
        geotiff_path=tif,
        metadata_path=metadata,
        product="no2",
        stride=2,
    )

    assert result["statistics"]["count"] == 10
    assert result["statistics"]["min"] == -1.0
    assert result["statistics"]["max"] == 12.0
    assert result["coverage"]["valid_pixel_count"] == 10
    assert result["coverage"]["total_pixel_count"] == 12


def test_stride_downsamples_without_interpolation(tmp_path):
    tif, metadata = _write_fixture(tmp_path)
    result = read_satellite_field(
        geotiff_path=tif,
        metadata_path=metadata,
        product="no2",
        stride=2,
    )

    assert result["grid"]["width"] == 2
    assert result["grid"]["height"] == 2
    assert result["longitude"] == pytest.approx([26.025, 26.125])
    assert result["latitude"] == pytest.approx([47.875, 47.975])


def test_semantics_never_claim_surface_concentration(tmp_path):
    tif, metadata = _write_fixture(tmp_path)
    result = read_satellite_field(
        geotiff_path=tif,
        metadata_path=metadata,
        product="no2",
    )
    semantics = result["semantics"]
    assert semantics["kind"] == "satellite_observation"
    assert semantics["model_forecast"] is False
    assert semantics["station_measurement"] is False
    assert semantics["surface_concentration"] is False


def test_day_window_is_strictly_under_24_hours():
    start, end = _day_window(date(2026, 9, 20))
    assert (end - start).total_seconds() == 86399


def test_invalid_stride_rejected(tmp_path):
    tif, metadata = _write_fixture(tmp_path)
    with pytest.raises(ValueError, match="stride"):
        read_satellite_field(
            geotiff_path=tif,
            metadata_path=metadata,
            product="no2",
            stride=0,
        )


def test_latest_available_skips_empty_current_day(tmp_path):
    empty = _write_fixture(tmp_path, name="empty", valid=False)
    valid = _write_fixture(tmp_path, name="valid", valid=True)

    provider = FakeProvider(
        {
            "2026-09-20": empty,
            "2026-09-19": valid,
        }
    )

    field = fetch_latest_available_satellite_field(
        product="no2",
        timeliness="NRTI",
        stride=2,
        max_lookback_days=3,
        provider=provider,
        reference_day=date(2026, 9, 20),
    )

    assert provider.calls == ["2026-09-20", "2026-09-19"]
    assert field["coverage"]["valid_pixel_count"] == 10
    assert field["selection"]["mode"] == "latest_available"
    assert field["selection"]["resolved_date"] == "2026-09-19"
    assert field["selection"]["lookback_days"] == 1
    assert field["selection"]["candidates_checked"] == [
        "2026-09-20",
        "2026-09-19",
    ]


def test_latest_available_uses_current_day_when_non_empty(tmp_path):
    valid = _write_fixture(tmp_path, name="valid", valid=True)
    provider = FakeProvider({"2026-09-20": valid})

    field = fetch_latest_available_satellite_field(
        product="no2",
        timeliness="NRTI",
        stride=1,
        max_lookback_days=3,
        provider=provider,
        reference_day=date(2026, 9, 20),
    )

    assert provider.calls == ["2026-09-20"]
    assert field["selection"]["resolved_date"] == "2026-09-20"
    assert field["selection"]["lookback_days"] == 0


def test_latest_available_raises_if_horizon_empty(tmp_path):
    empty0 = _write_fixture(tmp_path, name="empty0", valid=False)
    empty1 = _write_fixture(tmp_path, name="empty1", valid=False)
    provider = FakeProvider(
        {
            "2026-09-20": empty0,
            "2026-09-19": empty1,
        }
    )

    with pytest.raises(Sentinel5PNoCoverageError):
        fetch_latest_available_satellite_field(
            product="no2",
            timeliness="NRTI",
            stride=1,
            max_lookback_days=1,
            provider=provider,
            reference_day=date(2026, 9, 20),
        )
