from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.ocean_data.drift_forecast import (
    FORCING_MODE_CURRENTS_PLUS_WIND,
    run_surface_drift,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WEATHER-1.3B live currents + wind OpenDrift probe"
    )
    parser.add_argument("--lon", type=float, default=37.8)
    parser.add_argument("--lat", type=float, default=44.6)
    parser.add_argument("--hours", type=int, default=6)
    parser.add_argument("--particles", type=int, default=100)
    args = parser.parse_args()

    payload = run_surface_drift(
        longitude=args.lon,
        latitude=args.lat,
        hours=args.hours,
        particles=args.particles,
        forcing_mode=FORCING_MODE_CURRENTS_PLUS_WIND,
        cache_ttl_seconds=0,
    )

    print("model:", payload.get("model"))
    print("scope:", payload.get("scope"))
    print(
        "wind_drift_factor:",
        payload.get("simulation", {}).get("wind_drift_factor"),
    )

    wind = payload.get("forcing", {}).get("wind")
    print("wind forcing:", wind)

    horizons = payload.get("horizons") or []
    for item in horizons:
        center = item.get("center")
        print(
            f"+{item.get('hours')} h",
            "particles=",
            item.get("particle_count"),
            "center=",
            center,
        )

    print("cache:", payload.get("cache"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
