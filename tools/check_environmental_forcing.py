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


from agents.ocean_data.environmental_forcing import (
    get_environmental_forcing,
)


def value_or_dash(value):
    return (
        "—"
        if value is None
        else value
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
        "--at",
        default=None,
    )

    args = parser.parse_args()

    payload = get_environmental_forcing(
        longitude=args.lon,
        latitude=args.lat,
        at=args.at,
        cache_ttl_seconds=0,
    )

    current = payload["current"]
    wave = payload["wave"]
    wind = payload["wind"]

    print(
        "OPENOIL V0.10 STEP 1 - ENVIRONMENTAL FORCING CHECK"
    )
    print(
        "Target:",
        payload["target_time"],
    )
    print(
        "Location:",
        payload["location"]["longitude"],
        payload["location"]["latitude"],
    )
    print()

    print("CURRENT / COPERNICUS")
    print(
        "Dataset:",
        current["dataset_id"],
    )
    print(
        "Valid:",
        current["valid_time"],
    )
    print(
        "u / v:",
        current["u_m_s"],
        current["v_m_s"],
        "m/s",
    )
    print(
        "Sampled ocean cell:",
        current["sampled_location"],
    )
    print(
        "Speed:",
        current["speed_m_s"],
        "m/s",
    )
    print(
        "Direction to:",
        value_or_dash(
            current[
                "direction_to_deg"
            ]
        ),
        "deg",
    )
    print()

    print("WAVES / COPERNICUS")
    print(
        "Dataset:",
        wave["dataset_id"],
    )
    print(
        "Valid:",
        wave["valid_time"],
    )
    print(
        "Sampled ocean cell:",
        wave["sampled_location"],
    )
    print(
        "Significant wave height:",
        wave[
            "significant_wave_height_m"
        ],
        "m",
    )
    print(
        "Stokes u / v:",
        wave["stokes_u_m_s"],
        wave["stokes_v_m_s"],
        "m/s",
    )
    print(
        "Stokes speed:",
        wave["stokes_speed_m_s"],
        "m/s",
    )
    print(
        "Stokes direction to:",
        value_or_dash(
            wave[
                "stokes_direction_to_deg"
            ]
        ),
        "deg",
    )
    print()

    print("WIND / ECMWF IFS")
    print(
        "Run:",
        wind["run_time"],
    )
    print(
        "Forecast step:",
        wind[
            "forecast_step_hours"
        ],
        "h",
    )
    print(
        "Valid:",
        wind["valid_time"],
    )
    print(
        "u10 / v10:",
        wind["u10_m_s"],
        wind["v10_m_s"],
        "m/s",
    )
    print(
        "Speed:",
        wind["speed_m_s"],
        "m/s",
    )
    print(
        "Direction from:",
        value_or_dash(
            wind[
                "direction_from_deg"
            ]
        ),
        "deg",
    )
    print()

    print("TIME ALIGNMENT / MINUTES")
    for key, value in (
        payload[
            "time_alignment_minutes"
        ].items()
    ):
        print(
            f"{key}: {value}"
        )

    print()
    print("OPENOIL-READY VARIABLES")
    for key, value in (
        payload[
            "openoil_ready_fields"
        ].items()
    ):
        print(
            f"{key}: {value}"
        )

    print()
    print(
        "Cache:",
        payload["cache"]["status"],
    )


if __name__ == "__main__":
    main()
