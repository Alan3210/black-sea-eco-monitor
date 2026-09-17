from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATASET_ID = "COPERNICUS/S1_GRD"

AOI_NAME = "Novorossiysk"
AOI_BBOX = [37.55, 44.55, 38.15, 44.95]

INSTRUMENT_MODE = "IW"
RESOLUTION_METERS = 10
REQUIRED_POLARIZATION = "VV"

DEFAULT_DAYS = 30
DEFAULT_LIMIT = 5
DEFAULT_OUTPUT = Path("validation/gee_sentinel1_probe.json")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Non-destructive Sentinel-1 GRD access probe for the "
            "EkoKontur Black Sea project."
        )
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GEE_PROJECT_ID"),
        help="Google Cloud project registered for Earth Engine.",
    )
    parser.add_argument(
        "--authenticate",
        action="store_true",
        help="Run interactive ee.Authenticate() before ee.Initialize().",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Lookback window in days (default: {DEFAULT_DAYS}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Maximum scene metadata records to save (default: {DEFAULT_LIMIT}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSON output path (default: {DEFAULT_OUTPUT}).",
    )
    return parser


def _initialize_earth_engine(ee, project: str, authenticate: bool) -> None:
    if authenticate:
        print("Starting Earth Engine interactive authentication...")
        ee.Authenticate()

    ee.Initialize(project=project)


def _build_collection(ee, roi, start: datetime, end: datetime):
    return (
        ee.ImageCollection(DATASET_ID)
        .filterBounds(roi)
        .filterDate(start.isoformat(), end.isoformat())
        .filter(ee.Filter.eq("instrumentMode", INSTRUMENT_MODE))
        .filter(ee.Filter.eq("resolution_meters", RESOLUTION_METERS))
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation",
                REQUIRED_POLARIZATION,
            )
        )
        .sort("system:time_start", False)
    )


def _read_scene_metadata(ee, image) -> dict:
    metadata = ee.Dictionary(
        {
            "scene_id": image.id(),
            "system_index": image.get("system:index"),
            "acquisition_time": ee.Date(
                image.get("system:time_start")
            ).format("YYYY-MM-dd'T'HH:mm:ss'Z'"),
            "platform_number": image.get("platform_number"),
            "instrument_mode": image.get("instrumentMode"),
            "polarizations": image.get("transmitterReceiverPolarisation"),
            "orbit_pass": image.get("orbitProperties_pass"),
            "relative_orbit": image.get("relativeOrbitNumber_start"),
            "resolution_meters": image.get("resolution_meters"),
            "footprint_bounds_coordinates": (
                image.geometry()
                .bounds(maxError=100)
                .coordinates()
            ),
        }
    ).getInfo()

    coordinates = metadata.pop("footprint_bounds_coordinates", None)
    metadata["footprint_bounds"] = (
        {
            "type": "Polygon",
            "coordinates": coordinates,
        }
        if coordinates
        else None
    )

    return metadata


def main() -> int:
    args = _build_parser().parse_args()

    if not args.project:
        print("ERROR: provide --project or set GEE_PROJECT_ID.")
        return 2

    try:
        import ee
    except ImportError:
        print(
            "ERROR: earthengine-api is not installed. "
            "Install it with: python -m pip install earthengine-api"
        )
        return 3

    try:
        _initialize_earth_engine(
            ee=ee,
            project=args.project,
            authenticate=args.authenticate,
        )
    except Exception as exc:
        print(
            "ERROR: Earth Engine initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )
        return 4

    end = _utc_now()
    start = end - timedelta(days=max(1, args.days))
    limit = max(1, args.limit)

    roi = ee.Geometry.Rectangle(
        AOI_BBOX,
        proj=None,
        geodesic=False,
    )

    try:
        collection = _build_collection(
            ee=ee,
            roi=roi,
            start=start,
            end=end,
        )

        scene_count = int(collection.size().getInfo())
        saved_scene_count = min(scene_count, limit)

        scene_list = collection.toList(saved_scene_count)
        scenes = []

        for index in range(saved_scene_count):
            image = ee.Image(scene_list.get(index))
            scenes.append(_read_scene_metadata(ee, image))

    except Exception as exc:
        print(
            "ERROR: Sentinel-1 query failed: "
            f"{type(exc).__name__}: {exc}"
        )
        return 5

    payload = {
        "probe_version": "0.1",
        "information_type": "satellite_observation",
        "derivation_level": "processed",
        "generated_at": end.isoformat(),
        "aoi": {
            "name": AOI_NAME,
            "bbox": AOI_BBOX,
        },
        "query": {
            "dataset_id": DATASET_ID,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "instrument_mode": INSTRUMENT_MODE,
            "resolution_meters": RESOLUTION_METERS,
            "required_polarization": REQUIRED_POLARIZATION,
            "scene_limit": limit,
        },
        "provenance": {
            "data_provider": "Copernicus Sentinel-1",
            "processing_platform": "Google Earth Engine",
            "dataset_id": DATASET_ID,
            "source_level": "GRD",
            "gee_representation": "sigma0_backscatter_db",
        },
        "scene_count": scene_count,
        "saved_scene_count": len(scenes),
        "scenes": scenes,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Earth Engine initialization: OK")
    print(f"Project: {args.project}")
    print(f"Dataset: {DATASET_ID}")
    print(f"AOI: {AOI_NAME}")
    print(f"Window: {start.date().isoformat()} .. {end.date().isoformat()}")
    print(f"Matching scenes: {scene_count}")
    print(f"Saved scene metadata: {len(scenes)}")
    print(f"Output: {args.output}")
    print("Probe completed successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
