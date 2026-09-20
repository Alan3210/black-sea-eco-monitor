from __future__ import annotations

import argparse
import json
import sys

from backend.services.air_model_crosscheck import (
    AirModelCrosscheckError,
    AirModelCrosscheckUnavailable,
    fetch_time_aligned_crosscheck,
)
from backend.services.cams_air_field import CamsAirFieldError
from backend.services.cams_air_quality_provider import CamsAirQualityError
from backend.services.geos_cf_provider import GeosCFError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIR-1.5C CAMS/GEOS-CF time-aligned cross-check probe."
    )
    parser.add_argument(
        "--product",
        choices=["pm25", "pm10"],
        default="pm25",
    )
    parser.add_argument("--geos-time-index", type=int, default=0)
    parser.add_argument("--geos-stride", type=int, default=1)
    parser.add_argument("--cams-stride", type=int, default=1)
    parser.add_argument(
        "--max-time-gap-minutes",
        type=float,
        default=45.0,
    )
    args = parser.parse_args()

    try:
        result = fetch_time_aligned_crosscheck(
            product=args.product,
            geos_time_index=args.geos_time_index,
            geos_stride=args.geos_stride,
            cams_stride=args.cams_stride,
            max_time_gap_minutes=args.max_time_gap_minutes,
        )
    except (
        AirModelCrosscheckError,
        AirModelCrosscheckUnavailable,
        CamsAirFieldError,
        CamsAirQualityError,
        GeosCFError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}")
        return 2

    summary = {
        "kind": result["kind"],
        "product": result["product"],
        "units": result["units"],
        "semantics": result["semantics"],
        "time_alignment": result["time_alignment"],
        "spatial_alignment": result["spatial_alignment"],
        "metrics": result["metrics"],
        "sources": result["sources"],
    }

    print(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
