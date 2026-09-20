from __future__ import annotations

from backend.services.air_model_crosscheck import (
    _extract_grid_payload,
    _field_arrays,
    build_model_crosscheck,
)


def _real_cams_shape():
    latitudes = [39.05, 39.15, 39.25]
    longitudes = [26.05, 26.15, 26.25, 26.35]
    values = [
        [10.0, 11.0, 12.0, 13.0],
        [12.0, 13.0, 14.0, 15.0],
        [14.0, 15.0, 16.0, 17.0],
    ]
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
            "latitude_order": "ascending",
            "longitude_order": "ascending",
            "stride": 1,
            "latitudes": latitudes,
            "longitudes": longitudes,
            "values": values,
            "shape": [3, 4],
            "bbox": {
                "south": 39.05,
                "north": 39.25,
                "west": 26.05,
                "east": 26.35,
            },
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
        "longitude": [26.10, 26.20, 26.30],
        "latitude": [39.10, 39.20],
        "values": [
            [11.5, 12.5, 13.5],
            [13.5, 14.5, 15.5],
        ],
    }


def test_extracts_plural_cams_grid_coordinate_keys():
    lon, lat, values = _extract_grid_payload(_real_cams_shape())
    assert lon == [26.05, 26.15, 26.25, 26.35]
    assert lat == [39.05, 39.15, 39.25]
    assert len(values) == 3
    assert len(values[0]) == 4


def test_field_arrays_match_confirmed_real_cams_shape():
    lon, lat, values = _field_arrays(_real_cams_shape())
    assert lon.shape == (4,)
    assert lat.shape == (3,)
    assert values.shape == (3, 4)


def test_crosscheck_runs_with_plural_cams_grid_keys():
    result = build_model_crosscheck(
        cams_field=_real_cams_shape(),
        geos_field=_geos(),
    )

    assert result["spatial_alignment"]["compared_points"] == 6
    assert result["metrics"]["count"] == 6
    assert result["time_alignment"]["absolute_gap_minutes"] == 30.0


def test_top_level_plural_coordinate_keys_are_also_supported():
    field = {
        "longitudes": [26.0, 26.1],
        "latitudes": [39.0, 39.1],
        "values": [[1.0, 2.0], [3.0, 4.0]],
    }

    lon, lat, values = _field_arrays(field)
    assert lon.tolist() == [26.0, 26.1]
    assert lat.tolist() == [39.0, 39.1]
    assert values.shape == (2, 2)
