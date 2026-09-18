from copy import deepcopy
import pytest
from tools.gee_sentinel1_vv_calibration_v01 import (
    CalibrationError, build_output_skeleton, get_aoi_bbox,
    normalize_percentile_result, select_probe_scene, threshold_key,
)

@pytest.fixture
def probe():
    return {
        "information_type":"satellite_observation",
        "aoi":{"name":"Novorossiysk","bbox":[37.55,44.55,38.15,44.95]},
        "query":{"dataset_id":"COPERNICUS/S1_GRD"},
        "provenance":{
            "data_provider":"Copernicus Sentinel-1",
            "processing_platform":"Google Earth Engine",
            "source_level":"GRD",
            "gee_representation":"sigma0_backscatter_db",
        },
        "scenes":[{
            "scene_id":"S1D_TEST_SCENE",
            "system_index":"S1D_TEST_SCENE",
            "acquisition_time":"2026-09-17T03:31:58Z",
            "platform_number":"D",
            "orbit_pass":"DESCENDING",
            "relative_orbit":21,
            "instrument_mode":"IW",
            "polarizations":["VV","VH"],
            "resolution_meters":10,
        }],
    }

def test_select_scene(probe):
    scene = select_probe_scene(probe, 0)
    assert scene["scene_id"] == "S1D_TEST_SCENE"
    assert scene["relative_orbit"] == 21

def test_reject_wrong_information_type(probe):
    broken = deepcopy(probe)
    broken["information_type"] = "model_forecast"
    with pytest.raises(CalibrationError):
        select_probe_scene(broken, 0)

def test_reject_bad_index(probe):
    with pytest.raises(CalibrationError):
        select_probe_scene(probe, 3)

def test_bbox(probe):
    assert get_aoi_bbox(probe) == [37.55,44.55,38.15,44.95]

def test_output_semantics(probe):
    out = build_output_skeleton(probe, select_probe_scene(probe,0))
    assert out["information_type"] == "satellite_observation"
    assert out["derivation_level"] == "processed"
    assert out["analysis_type"] == "sar_vv_calibration"
    assert out["water_mask"]["class_value"] == 80
    assert out["edge_mask"]["edge_noise_floor_db"] == -30.0
    assert "oil_spill" in out["semantics"]["does_not_mean"]

def test_percentile_normalization():
    raw = {
        "VV_p01":-28.1,"VV_p05":-25.2,"VV_p10":-23.8,
        "VV_p25":-20.1,"VV_p50":-16.7,
    }
    assert normalize_percentile_result(raw) == {
        "p01":-28.1,"p05":-25.2,"p10":-23.8,
        "p25":-20.1,"p50":-16.7,
    }

def test_threshold_key():
    assert threshold_key(-18.0) == "-18"
    assert threshold_key(-22.5) == "-22.5"
