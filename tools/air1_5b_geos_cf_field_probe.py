from __future__ import annotations

import argparse
import json
import sys

from backend.services.geos_cf_field import fetch_geos_cf_field
from backend.services.geos_cf_provider import (
    PRODUCTS,
    GeosCFError,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIR-1.5B canonical GEOS-CF field probe."
    )
    parser.add_argument(
        "--product",
        default="pm25",
        choices=sorted(PRODUCTS),
    )
    parser.add_argument("--time-index", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1)
    args = parser.parse_args()

    try:
        field = fetch_geos_cf_field(
            product=args.product,
            time_index=args.time_index,
            stride=args.stride,
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
            "semantics",
            "run_time",
            "first_valid_time",
            "valid_time",
            "forecast_time_index",
            "lead_hours_from_nominal_run",
            "freshness",
            "cams_comparison",
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

    # ASCII-safe output avoids Windows PowerShell legacy-codepage mojibake.
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
