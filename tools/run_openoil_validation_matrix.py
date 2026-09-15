from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


from agents.ocean_data.openoil_validation_matrix import (
    DEFAULT_SCENARIOS,
    PROFILE_CONFIGS,
    build_validation_cases,
    run_validation_matrix,
)


def default_output_dir() -> Path:
    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    return (
        REPO_ROOT
        / "validation"
        / f"openoil-matrix-{stamp}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the Black Sea OpenOil sensitivity/coastline validation matrix."
        )
    )

    parser.add_argument(
        "--profile",
        choices=tuple(
            PROFILE_CONFIGS
        ),
        default="smoke",
    )
    parser.add_argument(
        "--at",
        default=None,
        help=(
            "Fixed UTC/ISO simulation start. "
            "If omitted, current model hour is captured once for the whole matrix."
        ),
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        default=None,
        help=(
            "Scenario key. Repeat to select several. "
            "Omit to run all built-in scenarios."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    if args.list_scenarios:
        for scenario in DEFAULT_SCENARIOS:
            print(
                f"{scenario.key}: "
                f"{scenario.longitude}, {scenario.latitude} "
                f"— {scenario.description}"
            )
        return

    cases = build_validation_cases(
        profile=args.profile,
        scenario_keys=args.scenarios,
    )

    if args.dry_run:
        print(
            f"PROFILE: {args.profile}"
        )
        print(
            f"CASES: {len(cases)}"
        )

        for case in cases:
            print(
                f"{case.scenario.key} | "
                f"{case.hours}h | "
                f"{case.particles} particles | "
                f"bbox ±{case.half_width_deg:g}°"
            )
        return

    output_dir = (
        Path(
            args.output_dir
        )
        if args.output_dir
        else default_output_dir()
    )

    print(
        "OPENOIL VALIDATION MATRIX"
    )
    print(
        f"Profile: {args.profile}"
    )
    print(
        f"Cases: {len(cases)}"
    )
    print(
        f"Output: {output_dir}"
    )
    print()

    def progress(message: str):
        print(
            message,
            flush=True,
        )

    result = run_validation_matrix(
        profile=args.profile,
        at=args.at,
        output_dir=output_dir,
        scenario_keys=args.scenarios,
        resume=not args.no_resume,
        progress_callback=progress,
    )

    print()
    print(
        "DONE"
    )
    print(
        f"Cases: {result['case_count']}"
    )
    print(
        f"Runtime: {result['elapsed_seconds'] / 60:.1f} min"
    )
    print(
        f"Summary: {output_dir / 'summary.txt'}"
    )
    print(
        f"CSV: {output_dir / 'summary.csv'}"
    )
    print(
        f"JSON: {output_dir / 'results.json'}"
    )


if __name__ == "__main__":
    main()
