from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


from agents.ocean_data.drift_forecast import (
    run_surface_drift,
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--lon",
        type=float,
        default=37.7691,
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=44.7240,
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=6,
    )
    parser.add_argument(
        "--particles",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--radius-m",
        type=float,
        default=500,
    )
    parser.add_argument(
        "--diffusivity",
        type=float,
        default=2,
    )
    parser.add_argument(
        "--at",
        default=None,
    )

    args = parser.parse_args()

    payload = run_surface_drift(
        longitude=args.lon,
        latitude=args.lat,
        at=args.at,
        hours=args.hours,
        particles=args.particles,
        radius_m=args.radius_m,
        diffusivity_m2_s=args.diffusivity,
        cache_ttl_seconds=0,
    )

    print(
        "OCEAN DRIFT V0.9 STEP 1 - LIVE CHECK"
    )
    print(
        "Model:",
        payload.get(
            "model",
        ),
    )
    print(
        "OpenDrift:",
        payload.get(
            "model_version",
        ),
    )
    print(
        "Scope:",
        payload.get(
            "scope",
        ),
    )

    seed = payload.get(
        "seed",
        {},
    )
    print(
        "Seed:",
        seed.get(
            "longitude",
        ),
        seed.get(
            "latitude",
        ),
    )
    print(
        "Particles:",
        seed.get(
            "particle_count",
        ),
    )

    simulation = payload.get(
        "simulation",
        {},
    )

    print(
        "Start:",
        simulation.get(
            "start_time",
        ),
    )
    print(
        "Forecast:",
        simulation.get(
            "forecast_hours",
        ),
        "h",
    )
    print(
        "Diffusivity:",
        simulation.get(
            "horizontal_diffusivity_m2_s",
        ),
        "m2/s",
    )

    print()

    for snapshot in payload.get(
        "horizons",
        [],
    ):
        center = (
            snapshot.get(
                "center",
            )
            or {}
        )

        print(
            f"+{snapshot['hours']:>2} h | "
            f"particles={snapshot['particle_count']} | "
            f"center="
            f"{center.get('longitude')},"
            f"{center.get('latitude')}"
        )

    cache = payload.get(
        "cache",
        {},
    )

    print()
    print(
        "Cache:",
        cache.get(
            "status",
        ),
    )


if __name__ == "__main__":
    main()
