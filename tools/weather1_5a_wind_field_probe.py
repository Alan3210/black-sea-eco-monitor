from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.wind_field import (
    EcmwfWindFieldService,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "WEATHER-1.5A live ECMWF Black Sea wind-field probe"
        )
    )
    parser.add_argument(
        "--at",
        default=None,
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=2,
    )
    args = parser.parse_args()

    payload = EcmwfWindFieldService().get_field(
        at=args.at,
        stride=args.stride,
    )

    print("provider:", payload["provider"])
    print("model:", payload["model"])
    print("height_m:", payload["height_m"])
    print(
        "forecast_reference_time:",
        payload["forecast_reference_time"],
    )
    print("valid_time:", payload["valid_time"])
    print("sources:", payload["sources"])
    print(
        "fallback_used:",
        payload["fallback_used"],
    )
    print(
        "temporal_interpolation:",
        payload["temporal_interpolation"],
    )
    print(
        "native_grid_shape:",
        payload["native_grid_shape"],
    )
    print("stride:", payload["stride"])
    print(
        "vector_count:",
        payload["vector_count"],
    )
    print(
        "speed_stats:",
        payload["speed_stats"],
    )

    if payload["vectors"]:
        print(
            "sample_vector:",
            payload["vectors"][
                len(payload["vectors"]) // 2
            ],
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
