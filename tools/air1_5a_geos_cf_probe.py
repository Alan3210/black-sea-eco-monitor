from __future__ import annotations

import argparse
import json
import sys

from backend.services.geos_cf_provider import (
    PRODUCTS,
    GeosCFError,
    GeosCFProvider,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIR-1.5A live NASA GEOS-CF v2 provider probe."
    )
    parser.add_argument(
        "--product",
        default="pm25",
        choices=sorted(PRODUCTS),
    )
    parser.add_argument(
        "--time-index",
        type=int,
        default=0,
        help="GEOS-CF latest-run hourly forecast index, 0..119.",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--force",
        action="store_true",
    )
    args = parser.parse_args()

    provider = GeosCFProvider()

    try:
        field = provider.fetch_field(
            product=args.product,
            time_index=args.time_index,
            stride=args.stride,
            force=args.force,
        )
    except (GeosCFError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    summary = {
        key: field[key]
        for key in (
            "provider",
            "model",
            "dataset",
            "product",
            "source_variable",
            "quantity",
            "units",
            "source_units",
            "product_note",
            "semantics",
            "run_time",
            "first_valid_time",
            "valid_time",
            "forecast_time_index",
            "lead_hours_from_nominal_run",
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
