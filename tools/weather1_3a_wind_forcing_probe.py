from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.ecmwf_wind_forcing import (
    EcmwfWindForcingBuilder,
    build_opendrift_wind_reader,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WEATHER-1.3A ECMWF wind forcing cube live probe"
    )
    parser.add_argument("--lon", type=float, default=37.8)
    parser.add_argument("--lat", type=float, default=44.6)
    parser.add_argument("--hours", type=int, default=12)
    parser.add_argument("--margin", type=float, default=2.0)
    args = parser.parse_args()

    start = datetime.now(timezone.utc).replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    bbox = {
        "west": args.lon - args.margin,
        "east": args.lon + args.margin,
        "south": args.lat - args.margin,
        "north": args.lat + args.margin,
    }

    builder = EcmwfWindForcingBuilder()
    forcing = builder.build(
        start_time=start,
        hours=args.hours,
        bbox=bbox,
    )
    reader = build_opendrift_wind_reader(
        forcing
    )

    print("run:", forcing.forecast_reference_time.isoformat())
    print("simulation start:", forcing.start_time.isoformat())
    print("simulation end:", forcing.end_time.isoformat())
    print("steps:", forcing.steps)
    print("sources:", forcing.sources)
    print("fallback_used:", forcing.fallback_used)
    print("cube sizes:", dict(forcing.dataset.sizes))
    print("cube variables:", list(forcing.dataset.data_vars))
    print("reader variables:", reader.variables)
    print("reader start_time:", reader.start_time)
    print("reader end_time:", reader.end_time)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
