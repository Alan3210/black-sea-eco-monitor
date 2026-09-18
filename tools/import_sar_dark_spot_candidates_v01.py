from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(
    __file__
).resolve().parents[1]

if str(
    REPO_ROOT
) not in sys.path:
    sys.path.insert(
        0,
        str(
            REPO_ROOT
        ),
    )


from agents.news_agent.event_store import EventStore
from backend.services.satellite.dark_spot_import import (
    DarkSpotImportError,
    import_candidate_file,
)


DEFAULT_INPUT = (
    REPO_ROOT
    / "validation"
    / "gee_sentinel1_dark_spot_candidates_v01.json"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import SAT-7B SAR dark-spot candidates "
            "as derived SatelliteObservation records."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help=(
            "Optional EventStore database path. "
            "Omit to use canonical database/events.db."
        ),
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    store = (
        EventStore(
            args.db
        )
        if args.db is not None
        else EventStore()
    )

    try:
        results = import_candidate_file(
            store,
            args.input,
        )
    except DarkSpotImportError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    created_count = sum(
        1
        for item in results
        if item[
            "created"
        ]
    )

    print(
        json.dumps(
            {
                "candidate_count": len(
                    results
                ),
                "created_count": (
                    created_count
                ),
                "existing_count": (
                    len(results)
                    - created_count
                ),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
