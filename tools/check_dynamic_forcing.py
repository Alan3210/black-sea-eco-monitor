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


from agents.ocean_data.dynamic_forcing_validation import (
    validate_dynamic_forcing,
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
        "--half-width-deg",
        type=float,
        default=1.0,
    )

    args = parser.parse_args()

    payload = validate_dynamic_forcing(
        longitude=args.lon,
        latitude=args.lat,
        at=args.at,
        hours=args.hours,
        half_width_deg=args.half_width_deg,
    )

    print(
        "OPENOIL V0.10 STEP 2B.1 - DYNAMIC FORCING VALIDATION"
    )
    print(
        "Ready for dynamic OpenOil:",
        payload[
            "ready_for_dynamic_openoil"
        ],
    )
    print()

    print("WINDOW")
    print(
        "Start:",
        payload["window"][
            "start_time"
        ],
    )
    print(
        "End:",
        payload["window"][
            "end_time"
        ],
    )
    print(
        "Copernicus requested through:",
        payload["window"][
            "copernicus_request_end_time"
        ],
    )
    print(
        "Copernicus end padding:",
        payload["window"][
            "copernicus_end_padding_hours"
        ],
        "h",
    )
    print(
        "Hours:",
        payload["window"][
            "hours"
        ],
    )
    print(
        "BBox:",
        payload["window"][
            "bbox"
        ],
    )
    print()

    print("DATASETS")

    for key in (
        "current",
        "wave",
        "temperature",
        "salinity",
        "wind",
    ):
        item = payload[
            "datasets"
        ][
            key
        ]

        print()
        print(
            key.upper()
        )

        if "dataset_id" in item:
            print(
                "Dataset:",
                item[
                    "dataset_id"
                ],
            )

        if "source" in item:
            print(
                "Source:",
                item[
                    "source"
                ],
            )

        if "run_time" in item:
            print(
                "Run:",
                item[
                    "run_time"
                ],
            )
            print(
                "Steps:",
                item[
                    "steps"
                ],
            )

        print(
            "Time:",
            item[
                "time_start"
            ],
            "->",
            item[
                "time_end"
            ],
        )
        print(
            "Time count:",
            item[
                "time_count"
            ],
        )
        print(
            "Coverage OK:",
            item[
                "coverage_ok"
            ],
        )
        print(
            "Finite:",
            item[
                "finite_counts"
            ],
        )
        print(
            "Dimensions:",
            item[
                "dimensions"
            ],
        )

    print()
    print("OPENDRIFT READERS")

    for key, item in (
        payload[
            "readers"
        ].items()
    ):
        print()
        print(
            key.upper(),
        )
        print(
            "Created:",
            item[
                "created"
            ],
        )
        print(
            "Variables:",
            item[
                "variables"
            ],
        )
        print(
            "Reader time:",
            item[
                "start_time"
            ],
            "->",
            item[
                "end_time"
            ],
        )


if __name__ == "__main__":
    main()
