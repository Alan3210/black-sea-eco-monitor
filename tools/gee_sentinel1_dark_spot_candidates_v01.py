from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATASET_ID = "COPERNICUS/S1_GRD"
WORLD_COVER_DATASET = "ESA/WorldCover/v200"
WORLD_COVER_BAND = "Map"
WORLD_COVER_WATER_CLASS = 80

DEFAULT_PROBE = Path("validation/gee_sentinel1_probe.json")
DEFAULT_CALIBRATION = Path(
    "validation/gee_sentinel1_vv_calibration_v01.json"
)
DEFAULT_OUTPUT = Path(
    "validation/gee_sentinel1_dark_spot_candidates_v01.json"
)

DEFAULT_THRESHOLD_DB = -24.0
EDGE_NOISE_FLOOR_DB = -30.0
DEFAULT_MIN_AREA_KM2 = 0.01
DEFAULT_LIMIT = 50

SCALE_METERS = 10
MAX_PIXELS = 1_000_000_000
TILE_SCALE = 4
CONNECTED_PIXEL_MAX_SIZE = 1024


class CandidateExtractionError(ValueError):
    """Raised when SAT-7B input/configuration is invalid."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "SAT-7B Sentinel-1 SAR dark-spot candidate extraction. "
            "Produces derived candidate polygons only; it does not "
            "classify oil or confirm pollution."
        )
    )

    parser.add_argument(
        "--project",
        default=os.getenv("GEE_PROJECT_ID"),
        help=(
            "Google Cloud project registered for Earth Engine. "
            "Defaults to GEE_PROJECT_ID."
        ),
    )
    parser.add_argument(
        "--authenticate",
        action="store_true",
        help="Run ee.Authenticate() before ee.Initialize().",
    )
    parser.add_argument(
        "--probe",
        type=Path,
        default=DEFAULT_PROBE,
    )
    parser.add_argument(
        "--calibration",
        type=Path,
        default=DEFAULT_CALIBRATION,
    )
    parser.add_argument(
        "--scene-index",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--threshold-db",
        type=float,
        default=DEFAULT_THRESHOLD_DB,
    )
    parser.add_argument(
        "--min-area-km2",
        type=float,
        default=DEFAULT_MIN_AREA_KM2,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    return parser


def initialize_ee(
    ee,
    *,
    project: str,
    authenticate: bool,
) -> None:
    if authenticate:
        ee.Authenticate()

    ee.Initialize(
        project=project
    )


def load_json_object(
    path: str | Path,
    *,
    label: str,
) -> dict[str, Any]:
    json_path = Path(path)

    try:
        data = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise CandidateExtractionError(
            f"{label} file not found: {json_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise CandidateExtractionError(
            f"invalid {label} JSON: {json_path}"
        ) from exc

    if not isinstance(data, dict):
        raise CandidateExtractionError(
            f"{label} root must be a JSON object"
        )

    return data


def select_probe_scene(
    probe: dict[str, Any],
    *,
    scene_index: int,
) -> dict[str, Any]:
    if probe.get("information_type") != (
        "satellite_observation"
    ):
        raise CandidateExtractionError(
            "probe information_type must be "
            "'satellite_observation'"
        )

    scenes = probe.get("scenes")

    if not isinstance(scenes, list) or not scenes:
        raise CandidateExtractionError(
            "probe contains no saved scenes"
        )

    if (
        scene_index < 0
        or scene_index >= len(scenes)
    ):
        raise CandidateExtractionError(
            f"scene_index out of range: {scene_index}"
        )

    scene = scenes[scene_index]

    for field_name in (
        "scene_id",
        "system_index",
        "acquisition_time",
    ):
        value = scene.get(
            field_name
        )

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise CandidateExtractionError(
                f"selected scene missing {field_name}"
            )

    return scene


def get_aoi_bbox(
    probe: dict[str, Any],
) -> list[float]:
    aoi = probe.get("aoi")

    if not isinstance(aoi, dict):
        raise CandidateExtractionError(
            "probe aoi must be an object"
        )

    bbox = aoi.get("bbox")

    if (
        not isinstance(bbox, list)
        or len(bbox) != 4
    ):
        raise CandidateExtractionError(
            "probe aoi.bbox must contain four values"
        )

    try:
        values = [
            float(value)
            for value in bbox
        ]
    except (TypeError, ValueError) as exc:
        raise CandidateExtractionError(
            "probe aoi.bbox values must be numeric"
        ) from exc

    min_lon, min_lat, max_lon, max_lat = values

    if (
        min_lon >= max_lon
        or min_lat >= max_lat
    ):
        raise CandidateExtractionError(
            "probe aoi.bbox has invalid bounds"
        )

    return values


def validate_calibration_scene(
    calibration: dict[str, Any],
    scene: dict[str, Any],
) -> None:
    if calibration.get("analysis_type") != (
        "sar_vv_calibration"
    ):
        raise CandidateExtractionError(
            "calibration analysis_type must be "
            "'sar_vv_calibration'"
        )

    calibration_scene = calibration.get(
        "scene"
    )

    if not isinstance(
        calibration_scene,
        dict,
    ):
        raise CandidateExtractionError(
            "calibration scene metadata missing"
        )

    if calibration_scene.get(
        "scene_id"
    ) != scene.get(
        "scene_id"
    ):
        raise CandidateExtractionError(
            "calibration scene does not match "
            "selected probe scene"
        )


def min_connected_pixels(
    *,
    min_area_km2: float,
    scale_meters: int = SCALE_METERS,
) -> int:
    if min_area_km2 <= 0:
        raise CandidateExtractionError(
            "min_area_km2 must be greater than zero"
        )

    pixel_area_m2 = (
        float(scale_meters)
        * float(scale_meters)
    )
    area_m2 = (
        float(min_area_km2)
        * 1_000_000.0
    )

    return max(
        1,
        int(
            math.ceil(
                area_m2 / pixel_area_m2
            )
        ),
    )


def validate_threshold(
    threshold_db: float,
) -> float:
    threshold_db = float(
        threshold_db
    )

    if not (
        EDGE_NOISE_FLOOR_DB
        < threshold_db
        < 0.0
    ):
        raise CandidateExtractionError(
            "threshold_db must be greater than "
            f"{EDGE_NOISE_FLOOR_DB} dB and below 0 dB"
        )

    return threshold_db


def bbox_from_geojson_geometry(
    geometry: dict[str, Any],
) -> list[float] | None:
    if not isinstance(
        geometry,
        dict,
    ):
        return None

    positions: list[
        tuple[float, float]
    ] = []

    def collect(value):
        if (
            isinstance(value, list)
            and len(value) >= 2
            and isinstance(
                value[0],
                (int, float),
            )
            and isinstance(
                value[1],
                (int, float),
            )
        ):
            positions.append(
                (
                    float(value[0]),
                    float(value[1]),
                )
            )
            return

        if isinstance(
            value,
            list,
        ):
            for item in value:
                collect(
                    item
                )

    collect(
        geometry.get(
            "coordinates"
        )
    )

    if not positions:
        return None

    lons = [
        item[0]
        for item in positions
    ]
    lats = [
        item[1]
        for item in positions
    ]

    return [
        min(lons),
        min(lats),
        max(lons),
        max(lats),
    ]


def normalize_candidate_features(
    feature_collection: dict[str, Any],
) -> list[dict[str, Any]]:
    features = feature_collection.get(
        "features",
        []
    )

    if not isinstance(
        features,
        list,
    ):
        raise CandidateExtractionError(
            "candidate FeatureCollection has invalid features"
        )

    normalized = []

    for index, feature in enumerate(
        features,
        start=1,
    ):
        geometry = feature.get(
            "geometry"
        )
        properties = feature.get(
            "properties"
        ) or {}

        area_m2 = properties.get(
            "area_m2"
        )

        if area_m2 is None:
            continue

        normalized.append(
            {
                "candidate_id": (
                    f"sar_ds_{index:03d}"
                ),
                "review_status": (
                    "unreviewed"
                ),
                "confidence": None,
                "area_km2": (
                    float(area_m2)
                    / 1_000_000.0
                ),
                "mean_vv_db": (
                    float(
                        properties[
                            "mean_vv_db"
                        ]
                    )
                    if properties.get(
                        "mean_vv_db"
                    )
                    is not None
                    else None
                ),
                "bbox": (
                    bbox_from_geojson_geometry(
                        geometry
                    )
                ),
                "geometry": geometry,
            }
        )

    return normalized


def build_output_skeleton(
    probe: dict[str, Any],
    calibration: dict[str, Any],
    scene: dict[str, Any],
    *,
    threshold_db: float,
    min_area_km2: float,
    min_pixels: int,
) -> dict[str, Any]:
    provenance = (
        probe.get(
            "provenance"
        )
        or {}
    )

    return {
        "extraction_version": "0.1",
        "information_type": (
            "satellite_observation"
        ),
        "derivation_level": "derived",
        "observation_type": (
            "sar_dark_spot_candidate"
        ),
        "generated_at": utc_now_iso(),
        "source_scene": {
            "scene_id": scene.get(
                "scene_id"
            ),
            "system_index": scene.get(
                "system_index"
            ),
            "acquisition_time": scene.get(
                "acquisition_time"
            ),
            "platform_number": scene.get(
                "platform_number"
            ),
            "orbit_pass": scene.get(
                "orbit_pass"
            ),
            "relative_orbit": scene.get(
                "relative_orbit"
            ),
            "instrument_mode": scene.get(
                "instrument_mode"
            ),
            "polarizations": scene.get(
                "polarizations"
            ),
        },
        "aoi": probe.get(
            "aoi"
        ),
        "analysis": {
            "threshold_db": threshold_db,
            "edge_noise_floor_db": (
                EDGE_NOISE_FLOOR_DB
            ),
            "min_area_km2": min_area_km2,
            "min_connected_pixels": (
                min_pixels
            ),
            "connectivity": 8,
            "scale_meters": SCALE_METERS,
            "water_mask": {
                "dataset_id": (
                    WORLD_COVER_DATASET
                ),
                "band": (
                    WORLD_COVER_BAND
                ),
                "class_value": (
                    WORLD_COVER_WATER_CLASS
                ),
                "class_label": (
                    "permanent_water_bodies"
                ),
            },
        },
        "calibration_reference": {
            "analysis_type": (
                calibration.get(
                    "analysis_type"
                )
            ),
            "calibration_version": (
                calibration.get(
                    "calibration_version"
                )
            ),
            "vv_db": calibration.get(
                "vv_db"
            ),
            "threshold_tests": (
                calibration.get(
                    "threshold_tests"
                )
            ),
        },
        "summary": {},
        "candidates": [],
        "provenance": {
            "data_provider": (
                provenance.get(
                    "data_provider",
                    "Copernicus Sentinel-1",
                )
            ),
            "processing_platform": (
                provenance.get(
                    "processing_platform",
                    "Google Earth Engine",
                )
            ),
            "dataset_id": (
                provenance.get(
                    "dataset_id",
                    DATASET_ID,
                )
            ),
            "source_level": (
                provenance.get(
                    "source_level",
                    "GRD",
                )
            ),
            "gee_representation": (
                provenance.get(
                    "gee_representation",
                    "sigma0_backscatter_db",
                )
            ),
            "processing_method": (
                "water_mask + edge_guard + "
                "vv_threshold + connected_components"
            ),
        },
        "semantics": {
            "result_type": (
                "sar_dark_spot_candidate"
            ),
            "confidence_meaning": (
                "not_assigned_in_v0.1"
            ),
            "does_not_mean": [
                "oil_spill",
                "confirmed_pollution",
                "confirmed_event",
                "causal_link_to_event",
            ],
        },
    }


def select_ee_scene(
    ee,
    *,
    system_index: str,
):
    image = (
        ee.ImageCollection(
            DATASET_ID
        )
        .filter(
            ee.Filter.eq(
                "system:index",
                system_index,
            )
        )
        .first()
    )

    return ee.Image(
        image
    )


def extract_candidates(
    ee,
    *,
    image,
    roi,
    threshold_db: float,
    min_pixels: int,
    limit: int,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
]:
    vv = image.select(
        "VV"
    )

    water_mask = (
        ee.ImageCollection(
            WORLD_COVER_DATASET
        )
        .mosaic()
        .select(
            WORLD_COVER_BAND
        )
        .eq(
            WORLD_COVER_WATER_CLASS
        )
    )

    valid_water_vv = (
        vv
        .updateMask(
            water_mask
        )
        .updateMask(
            vv.gt(
                EDGE_NOISE_FLOOR_DB
            )
        )
    )

    raw_dark_mask = (
        valid_water_vv
        .lt(
            threshold_db
        )
        .selfMask()
    )

    connected_count = (
        raw_dark_mask
        .connectedPixelCount(
            maxSize=CONNECTED_PIXEL_MAX_SIZE,
            eightConnected=True,
        )
    )

    filtered_mask = (
        raw_dark_mask
        .updateMask(
            connected_count.gte(
                min_pixels
            )
        )
        .rename(
            "candidate"
        )
        .toInt()
    )

    raw_area_m2 = (
        ee.Image.pixelArea()
        .updateMask(
            raw_dark_mask
        )
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi,
            scale=SCALE_METERS,
            maxPixels=MAX_PIXELS,
            bestEffort=True,
            tileScale=TILE_SCALE,
        )
        .get(
            "area"
        )
        .getInfo()
    )

    filtered_area_m2 = (
        ee.Image.pixelArea()
        .updateMask(
            filtered_mask
        )
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi,
            scale=SCALE_METERS,
            maxPixels=MAX_PIXELS,
            bestEffort=True,
            tileScale=TILE_SCALE,
        )
        .get(
            "area"
        )
        .getInfo()
    )

    vectors = (
        filtered_mask
        .reduceToVectors(
            reducer=ee.Reducer.countEvery(),
            geometry=roi,
            scale=SCALE_METERS,
            geometryType="polygon",
            eightConnected=True,
            labelProperty="label",
            maxPixels=MAX_PIXELS,
            tileScale=TILE_SCALE,
        )
    )

    def enrich(feature):
        geometry = feature.geometry()

        area_m2 = geometry.area(
            maxError=SCALE_METERS
        )

        mean_vv_db = (
            vv.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=SCALE_METERS,
                maxPixels=MAX_PIXELS,
                bestEffort=True,
                tileScale=TILE_SCALE,
            )
            .get(
                "VV"
            )
        )

        return feature.set(
            {
                "area_m2": area_m2,
                "mean_vv_db": (
                    mean_vv_db
                ),
            }
        )

    enriched = (
        vectors
        .map(
            enrich
        )
        .sort(
            "area_m2",
            False,
        )
    )

    total_candidate_count = int(
        enriched.size().getInfo()
    )

    saved = (
        enriched
        .limit(
            max(
                1,
                int(
                    limit
                ),
            )
        )
        .getInfo()
    )

    candidates = (
        normalize_candidate_features(
            saved
        )
    )

    summary = {
        "raw_dark_area_km2": (
            float(
                raw_area_m2
                or 0.0
            )
            / 1_000_000.0
        ),
        "filtered_candidate_area_km2": (
            float(
                filtered_area_m2
                or 0.0
            )
            / 1_000_000.0
        ),
        "candidate_count": (
            total_candidate_count
        ),
        "saved_candidate_count": (
            len(
                candidates
            )
        ),
    }

    return (
        summary,
        candidates,
    )


def main() -> int:
    args = build_parser().parse_args()

    if not args.project:
        print(
            "ERROR: provide --project or "
            "set GEE_PROJECT_ID."
        )
        return 2

    try:
        threshold_db = (
            validate_threshold(
                args.threshold_db
            )
        )

        min_pixels = (
            min_connected_pixels(
                min_area_km2=(
                    args.min_area_km2
                )
            )
        )

        probe = load_json_object(
            args.probe,
            label="probe",
        )
        calibration = (
            load_json_object(
                args.calibration,
                label="calibration",
            )
        )
        scene = select_probe_scene(
            probe,
            scene_index=(
                args.scene_index
            ),
        )
        validate_calibration_scene(
            calibration,
            scene,
        )
        bbox = get_aoi_bbox(
            probe
        )

    except CandidateExtractionError as exc:
        print(
            f"ERROR: {exc}"
        )
        return 3

    try:
        import ee
    except ImportError:
        print(
            "ERROR: earthengine-api is not installed."
        )
        return 4

    try:
        initialize_ee(
            ee,
            project=args.project,
            authenticate=(
                args.authenticate
            ),
        )

        roi = ee.Geometry.Rectangle(
            bbox,
            proj=None,
            geodesic=False,
        )

        image = select_ee_scene(
            ee,
            system_index=(
                scene[
                    "system_index"
                ]
            ),
        )

        summary, candidates = (
            extract_candidates(
                ee,
                image=image,
                roi=roi,
                threshold_db=(
                    threshold_db
                ),
                min_pixels=(
                    min_pixels
                ),
                limit=max(
                    1,
                    int(
                        args.limit
                    ),
                ),
            )
        )

    except Exception as exc:
        print(
            "ERROR: candidate extraction failed: "
            f"{type(exc).__name__}: {exc}"
        )
        return 5

    payload = build_output_skeleton(
        probe,
        calibration,
        scene,
        threshold_db=(
            threshold_db
        ),
        min_area_km2=(
            args.min_area_km2
        ),
        min_pixels=(
            min_pixels
        ),
    )

    payload[
        "summary"
    ] = summary

    payload[
        "candidates"
    ] = candidates

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "Earth Engine initialization: OK"
    )
    print(
        f"Scene: {scene['scene_id']}"
    )
    print(
        f"Threshold: VV < {threshold_db} dB"
    )
    print(
        "Minimum candidate area: "
        f"{args.min_area_km2} km2 "
        f"({min_pixels} connected pixels)"
    )
    print(
        "Raw dark area km2: "
        f"{summary['raw_dark_area_km2']:.3f}"
    )
    print(
        "Filtered candidate area km2: "
        f"{summary['filtered_candidate_area_km2']:.3f}"
    )
    print(
        "Candidate polygons: "
        f"{summary['candidate_count']}"
    )
    print(
        "Saved candidate polygons: "
        f"{summary['saved_candidate_count']}"
    )
    print(
        f"Output: {args.output}"
    )
    print(
        "SAT-7B dark-spot candidate extraction "
        "completed successfully."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
