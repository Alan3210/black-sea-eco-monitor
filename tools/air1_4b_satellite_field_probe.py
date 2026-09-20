from __future__ import annotations

import argparse
from datetime import date
import json
import sys

from backend.services.sentinel5p_provider import Sentinel5PError
from backend.services.sentinel5p_satellite_field import (
    DEFAULT_MAX_LOOKBACK_DAYS,
    Sentinel5PNoCoverageError,
    fetch_satellite_field,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIR-1.4B.1 canonical Sentinel-5P field probe."
    )
    parser.add_argument("--product", default="no2")
    parser.add_argument(
        "--date",
        dest="day",
        type=date.fromisoformat,
        default=None,
        help=(
            "Exact UTC day. If omitted, search latest available coverage."
        ),
    )
    parser.add_argument(
        "--timeliness",
        default="NRTI",
        choices=["NRTI", "OFFL", "RPRO"],
    )
    parser.add_argument("--stride", type=int, default=4)
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=DEFAULT_MAX_LOOKBACK_DAYS,
    )
    args = parser.parse_args()

    try:
        field = fetch_satellite_field(
            product=args.product,
            day=args.day,
            timeliness=args.timeliness,
            stride=args.stride,
            max_lookback_days=args.lookback_days,
        )
    except (
        Sentinel5PError,
        Sentinel5PNoCoverageError,
        ValueError,
        OSError,
    ) as exc:
        print(f"ERROR: {exc}")
        return 2

    summary = {
        key: field[key]
        for key in (
            "provider",
            "collection",
            "platform",
            "instrument",
            "product",
            "quantity",
            "units",
            "time_from",
            "time_to",
            "timeliness",
            "min_qa",
            "semantics",
            "selection",
            "bbox",
            "grid",
            "statistics",
            "coverage",
            "provenance",
        )
    }
    summary["sample"] = {
        "longitude_count": len(field["longitude"]),
        "latitude_count": len(field["latitude"]),
        "first_non_null": next(
            (
                value
                for row in field["values"]
                for value in row
                if value is not None
            ),
            None,
        ),
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
