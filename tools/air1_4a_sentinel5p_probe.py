from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import sys

from backend.services.sentinel5p_provider import (
    DEFAULT_BLACK_SEA_BBOX,
    PRODUCTS,
    Sentinel5PError,
    Sentinel5PProvider,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIR-1.4A live Sentinel-5P/TROPOMI probe."
    )
    parser.add_argument(
        "--product",
        default="no2",
        choices=sorted(PRODUCTS),
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=23.5,
        help="Look-back window, must be <=24 h.",
    )
    parser.add_argument(
        "--timeliness",
        default="NRTI",
        choices=["NRTI", "OFFL", "RPRO"],
    )
    parser.add_argument("--width", type=int, default=350)
    parser.add_argument("--height", type=int, default=180)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore cache and fetch again.",
    )
    args = parser.parse_args()

    if not os.getenv("CDSE_SH_CLIENT_ID") or not os.getenv(
        "CDSE_SH_CLIENT_SECRET"
    ):
        print("Missing Sentinel Hub OAuth credentials.")
        print("Set:")
        print('$env:CDSE_SH_CLIENT_ID="<client-id>"')
        print('$env:CDSE_SH_CLIENT_SECRET="<client-secret>"')
        return 2

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=args.hours)

    provider = Sentinel5PProvider()

    try:
        artifact = provider.fetch_geotiff(
            product=args.product,
            start=start,
            end=end,
            bbox=DEFAULT_BLACK_SEA_BBOX,
            width=args.width,
            height=args.height,
            timeliness=args.timeliness,
            force=args.force,
        )
    except (Sentinel5PError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 3

    m = artifact.metadata
    summary = {
        "status": "ok",
        "cache_hit": artifact.cache_hit,
        "product": m["product"],
        "band": m["band"],
        "quantity": m["quantity"],
        "units": m["units"],
        "time_from": m["time_from"],
        "time_to": m["time_to"],
        "timeliness": m["timeliness"],
        "min_qa": m["min_qa"],
        "bbox": m["bbox"],
        "grid": [m["height"], m["width"]],
        "bytes": m["bytes"],
        "sha256": m["sha256"],
        "geotiff": str(artifact.path),
        "metadata": str(artifact.metadata_path),
        "semantics": m["semantics"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
