from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Allow both:
#   python -m tools.weather1_1_ecmwf_point_probe
# and:
#   python .\tools\weather1_1_ecmwf_point_probe.py
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.ecmwf_weather_provider import (
    EcmwfOpenDataWeatherProvider,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WEATHER-1.1 ECMWF point-weather live probe"
    )
    parser.add_argument("--lat", type=float, default=44.60)
    parser.add_argument("--lon", type=float, default=37.80)
    args = parser.parse_args()

    provider = EcmwfOpenDataWeatherProvider()
    point = provider.get_point(
        latitude=args.lat,
        longitude=args.lon,
    )

    print(
        json.dumps(
            point.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
