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


from agents.ocean_data.openoil_validation import (
    run_openoil_engine_validation,
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

    args = parser.parse_args()

    payload = run_openoil_engine_validation(
        longitude=args.lon,
        latitude=args.lat,
        at=args.at,
        hours=args.hours,
        particles=args.particles,
        radius_m=args.radius_m,
        release_volume_m3=args.volume_m3,
        oil_type=args.oil_type,
    )

    print(
        "OPENOIL V0.10 STEP 2A - ENGINE VALIDATION"
    )
    print(
        "Status:",
        payload["forecast_status"],
    )
    print(
        "Model:",
        payload["model"],
    )
    print(
        "Weathering:",
        payload[
            "weathering_model"
        ],
    )
    print(
        "Oil type:",
        payload["oil_type"],
    )
    print()

    print("REQUESTED LOCATION")
    print(
        payload[
            "requested_location"
        ],
    )
    print()

    print("MODEL SEED LOCATION")
    print(
        payload[
            "model_seed_location"
        ],
    )
    print()

    print("RELEASE")
    print(
        payload["release"],
    )
    print()

    print("FORCING")
    forcing = payload[
        "forcing_snapshot"
    ]
    print(
        "Target:",
        forcing["target_time"],
    )
    print(
        "Current:",
        forcing["current"][
            "u_m_s"
        ],
        forcing["current"][
            "v_m_s"
        ],
        "m/s",
    )
    print(
        "Wind:",
        forcing["wind"][
            "u10_m_s"
        ],
        forcing["wind"][
            "v10_m_s"
        ],
        "m/s",
    )
    print(
        "Wave Hs:",
        forcing["wave"][
            "significant_wave_height_m"
        ],
        "m",
    )
    print(
        "Stokes:",
        forcing["wave"][
            "stokes_u_m_s"
        ],
        forcing["wave"][
            "stokes_v_m_s"
        ],
        "m/s",
    )
    print(
        "Temperature:",
        forcing[
            "temperature_c"
        ],
        "C (provisional constant)",
    )
    print(
        "Salinity:",
        forcing[
            "salinity_psu"
        ],
        "PSU (provisional constant)",
    )
    print()

    print("FINAL POSITIONS")
    print(
        payload[
            "final_positions"
        ],
    )
    final_positions = payload[
        "final_positions"
    ]
    if (
        final_positions.get(
            "trajectory_count"
        )
        != final_positions.get(
            "particle_count"
        )
    ):
        print(
            "WARNING: not every seeded trajectory has a recoverable "
            "last finite position."
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
        ],
    )
    print()

    print("IMPORTANT")
    print(
        "This is an OpenOil engine validation using a real start-time "
        "forcing snapshot held constant through the run."
    )
    print(
        "Do NOT present it as an operational oil-spill forecast."
    )


if __name__ == "__main__":
    main()
