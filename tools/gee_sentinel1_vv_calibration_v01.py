from __future__ import annotations
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

DATASET_ID = "COPERNICUS/S1_GRD"
WORLD_COVER_DATASET = "ESA/WorldCover/v200"
WORLD_COVER_BAND = "Map"
WORLD_COVER_WATER_CLASS = 80
DEFAULT_PROBE = Path("validation/gee_sentinel1_probe.json")
DEFAULT_OUTPUT = Path("validation/gee_sentinel1_vv_calibration_v01.json")
THRESHOLDS_DB = (-18.0, -20.0, -22.0, -24.0, -26.0, -28.0)
EDGE_NOISE_FLOOR_DB = -30.0
SCALE_METERS = 10
MAX_PIXELS = 1_000_000_000
TILE_SCALE = 4

class CalibrationError(ValueError):
    pass

def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

def build_parser():
    p = argparse.ArgumentParser(description="SAT-7A Sentinel-1 VV calibration probe")
    p.add_argument("--project", default=os.getenv("GEE_PROJECT_ID"))
    p.add_argument("--authenticate", action="store_true")
    p.add_argument("--probe", type=Path, default=DEFAULT_PROBE)
    p.add_argument("--scene-index", type=int, default=0)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return p

def initialize_ee(ee, project, authenticate):
    if authenticate:
        ee.Authenticate()
    ee.Initialize(project=project)

def load_probe(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CalibrationError(f"probe file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CalibrationError(f"invalid probe JSON: {path}") from exc
    if not isinstance(data, dict):
        raise CalibrationError("probe root must be a JSON object")
    return data

def select_probe_scene(probe, scene_index=0):
    if probe.get("information_type") != "satellite_observation":
        raise CalibrationError("probe information_type must be 'satellite_observation'")
    scenes = probe.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise CalibrationError("probe contains no saved scenes")
    if scene_index < 0 or scene_index >= len(scenes):
        raise CalibrationError(f"scene_index out of range: {scene_index}")
    scene = scenes[scene_index]
    for name in ("scene_id", "system_index", "acquisition_time"):
        if not isinstance(scene.get(name), str) or not scene[name].strip():
            raise CalibrationError(f"selected scene missing {name}")
    return scene

def get_aoi_bbox(probe):
    aoi = probe.get("aoi")
    if not isinstance(aoi, dict):
        raise CalibrationError("probe aoi must be an object")
    bbox = aoi.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        raise CalibrationError("probe aoi.bbox must contain four values")
    vals = [float(v) for v in bbox]
    if vals[0] >= vals[2] or vals[1] >= vals[3]:
        raise CalibrationError("probe aoi.bbox has invalid bounds")
    return vals

def normalize_percentile_result(raw):
    out = {}
    for name, pct in (("p01",1),("p05",5),("p10",10),("p25",25),("p50",50)):
        value = None
        for key in (name, f"VV_{name}", f"VV_p{pct}", f"VV_p{pct:02d}"):
            if key in raw:
                value = raw[key]
                break
        out[name] = float(value) if value is not None else None
    return out

def threshold_key(value):
    return str(int(value)) if float(value).is_integer() else str(value)

def build_output_skeleton(probe, scene):
    q = probe.get("query") or {}
    p = probe.get("provenance") or {}
    return {
        "calibration_version": "0.1",
        "information_type": "satellite_observation",
        "derivation_level": "processed",
        "analysis_type": "sar_vv_calibration",
        "generated_at": _utc_now_iso(),
        "scene": {
            "scene_id": scene.get("scene_id"),
            "system_index": scene.get("system_index"),
            "acquisition_time": scene.get("acquisition_time"),
            "platform_number": scene.get("platform_number"),
            "orbit_pass": scene.get("orbit_pass"),
            "relative_orbit": scene.get("relative_orbit"),
            "instrument_mode": scene.get("instrument_mode"),
            "polarizations": scene.get("polarizations"),
            "resolution_meters": scene.get("resolution_meters"),
        },
        "aoi": probe.get("aoi"),
        "source": {
            "dataset_id": q.get("dataset_id", DATASET_ID),
            "data_provider": p.get("data_provider", "Copernicus Sentinel-1"),
            "processing_platform": p.get("processing_platform", "Google Earth Engine"),
            "source_level": p.get("source_level", "GRD"),
            "representation": p.get("gee_representation", "sigma0_backscatter_db"),
        },
        "water_mask": {
            "dataset_id": WORLD_COVER_DATASET,
            "band": WORLD_COVER_BAND,
            "class_value": WORLD_COVER_WATER_CLASS,
            "class_label": "permanent_water_bodies",
        },
        "edge_mask": {
            "rule": "VV > edge_noise_floor_db",
            "edge_noise_floor_db": EDGE_NOISE_FLOOR_DB,
        },
        "scale_meters": SCALE_METERS,
        "vv_db": {},
        "threshold_tests": {},
        "semantics": {
            "result_type": "calibration_statistics_only",
            "does_not_mean": ["oil_spill", "confirmed_pollution", "confirmed_event"],
        },
    }

def select_ee_scene(ee, system_index):
    image = ee.ImageCollection(DATASET_ID).filter(
        ee.Filter.eq("system:index", system_index)
    ).first()
    return ee.Image(image)

def compute_statistics(ee, image, roi):
    vv = image.select("VV")
    world_cover = ee.ImageCollection(WORLD_COVER_DATASET).mosaic().select(WORLD_COVER_BAND)
    water_mask = world_cover.eq(WORLD_COVER_WATER_CLASS)
    valid = vv.updateMask(water_mask).updateMask(vv.gt(EDGE_NOISE_FLOOR_DB))

    reducer = ee.Reducer.percentile(
        [1,5,10,25,50],
        ["p01","p05","p10","p25","p50"],
    )
    raw = valid.reduceRegion(
        reducer=reducer, geometry=roi, scale=SCALE_METERS,
        maxPixels=MAX_PIXELS, bestEffort=True, tileScale=TILE_SCALE,
    ).getInfo() or {}

    pixel_count = valid.reduceRegion(
        reducer=ee.Reducer.count(), geometry=roi, scale=SCALE_METERS,
        maxPixels=MAX_PIXELS, bestEffort=True, tileScale=TILE_SCALE,
    ).get("VV").getInfo()

    valid_area_m2 = ee.Image.pixelArea().updateMask(valid.mask()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=SCALE_METERS,
        maxPixels=MAX_PIXELS, bestEffort=True, tileScale=TILE_SCALE,
    ).get("area").getInfo()

    valid_area_km2 = float(valid_area_m2 or 0.0) / 1_000_000.0
    tests = {}

    for t in THRESHOLDS_DB:
        mask = valid.lt(t)
        area_m2 = ee.Image.pixelArea().updateMask(mask).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=roi, scale=SCALE_METERS,
            maxPixels=MAX_PIXELS, bestEffort=True, tileScale=TILE_SCALE,
        ).get("area").getInfo()
        count = mask.updateMask(mask).reduceRegion(
            reducer=ee.Reducer.count(), geometry=roi, scale=SCALE_METERS,
            maxPixels=MAX_PIXELS, bestEffort=True, tileScale=TILE_SCALE,
        ).get("VV").getInfo()
        area_km2 = float(area_m2 or 0.0) / 1_000_000.0
        tests[threshold_key(t)] = {
            "threshold_db": t,
            "candidate_area_km2": area_km2,
            "candidate_pixel_count": int(count or 0),
            "fraction_of_valid_water_area": area_km2 / valid_area_km2 if valid_area_km2 else None,
        }

    return {
        "percentiles": normalize_percentile_result(raw),
        "valid_water_pixel_count": int(pixel_count or 0),
        "valid_water_area_km2": valid_area_km2,
    }, tests

def main():
    args = build_parser().parse_args()
    if not args.project:
        print("ERROR: provide --project or set GEE_PROJECT_ID.")
        return 2
    try:
        probe = load_probe(args.probe)
        scene = select_probe_scene(probe, args.scene_index)
        bbox = get_aoi_bbox(probe)
    except CalibrationError as exc:
        print(f"ERROR: {exc}")
        return 3
    try:
        import ee
    except ImportError:
        print("ERROR: earthengine-api is not installed.")
        return 4
    try:
        initialize_ee(ee, args.project, args.authenticate)
        roi = ee.Geometry.Rectangle(bbox, proj=None, geodesic=False)
        image = select_ee_scene(ee, scene["system_index"])
        vv_stats, threshold_tests = compute_statistics(ee, image, roi)
    except Exception as exc:
        print(f"ERROR: calibration query failed: {type(exc).__name__}: {exc}")
        return 5

    payload = build_output_skeleton(probe, scene)
    payload["vv_db"] = vv_stats
    payload["threshold_tests"] = threshold_tests

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Earth Engine initialization: OK")
    print(f"Scene: {scene['scene_id']}")
    print(f"Acquisition: {scene['acquisition_time']}")
    print(f"Valid water pixels: {vv_stats['valid_water_pixel_count']}")
    print(f"Valid water area km2: {vv_stats['valid_water_area_km2']:.3f}")
    print(f"VV percentiles dB: {vv_stats['percentiles']}")
    print("Threshold test areas km2:")
    for key, result in threshold_tests.items():
        print(f"  {key} dB -> {result['candidate_area_km2']:.3f} km2")
    print(f"Output: {args.output}")
    print("SAT-7A VV calibration completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
