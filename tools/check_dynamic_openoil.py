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


from agents.ocean_data.dynamic_openoil import (
    run_dynamic_openoil,
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
        default=200,
    )
    parser.add_argument(
        "--volume-m3",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "--oil-type",
        default=None,
    )
    parser.add_argument(
        "--half-width-deg",
        type=float,
        default=1.0,
    )

    args = parser.parse_args()

    payload = run_dynamic_openoil(
        longitude=args.lon,
        latitude=args.lat,
        at=args.at,
        hours=args.hours,
        particles=args.particles,
        radius_m=args.radius_m,
        release_volume_m3=args.volume_m3,
        oil_type=args.oil_type,
        half_width_deg=args.half_width_deg,
    )

    print(
        "OPENOIL V0.10 STEP 2B.2 - DYNAMIC OPENOIL"
    )
    print(
        "Status:",
        payload[
            "forecast_status"
        ],
    )
    print(
        "Forecast complete:",
        payload[
            "forecast_complete"
        ],
    )
    print(
        "Completion reason:",
        payload[
            "completion_reason"
        ],
    )
    print(
        "Oil type:",
        payload[
            "oil_type"
        ],
    )
    print()

    print("MODEL SEED LOCATION")
    print(
        payload[
            "model_seed_location"
        ]
    )
    print()

    print("SIMULATION")
    for key, value in (
        payload[
            "simulation"
        ].items()
    ):
        print(
            f"{key}: {value}"
        )
    print()

    print("RUNTIME STATE")
    for key, value in (
        payload[
            "runtime_state"
        ].items()
    ):
        print(
            f"{key}: {value}"
        )
    print()

    print("FORCING")
    for key, value in (
        payload[
            "forcing"
        ].items()
    ):
        print(
            f"{key}: {value}"
        )
    print()

    print("HORIZONS")
    for item in payload[
        "horizons"
    ]:
        center = (
            item.get(
                "center"
            )
            or {}
        )

        print(
            f"+{item['hours']:>2} h | "
            f"complete={item['horizon_complete']} | "
            f"actual={item['time']} | "
            f"particles={item['particle_count']} | "
            f"center="
            f"{center.get('longitude')},"
            f"{center.get('latitude')}"
        )
    print()

    if (
        not payload[
            "simulation"
        ][
            "reached_requested_end"
        ]
        and not payload[
            "runtime_state"
        ][
            "physical_terminal_state"
        ]
    ):
        print(
            "WARNING: OpenOil stopped before the requested end time "
            "for an unresolved reason."
        )
        print(
            "Do not interpret the last available state as the requested horizon."
        )
        print()
    elif payload[
        "runtime_state"
    ][
        "physical_terminal_state"
    ]:
        print(
            "TERMINAL STATE: all seeded particles were physically stranded "
            "before the requested end time."
        )
        print(
            "The final stranded state can be carried forward to the requested horizon."
        )
        print()

    print("FINAL POSITIONS")
    print(
        payload[
            "final_positions"
        ]
    )
    print()

    print("MASS BUDGET")
    for key, value in (
        payload[
            "mass_budget"
        ].items()
    ):
        print(
            f"{key}: {value}"
        )
    print()

    print("STATUS COUNTS")
    print(
        payload[
            "status_counts"
        ]
    )
    print()

    print("IMPORTANT")
    print(
        "Dynamic forcing is active, but this is still a scientific "
        "validation run until coastline/sensitivity checks are complete."
    )


if __name__ == "__main__":
    main()
