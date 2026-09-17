from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


from agents.news_agent.event_store import EventStore
from backend.services.satellite.gee_probe_import import (
    GeeProbeImportError,
    import_probe_file,
)


DEFAULT_PROBE = (
    REPO_ROOT
    / "validation"
    / "gee_sentinel1_probe.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Import one cached Sentinel-1 scene "
            "from the GEE access probe into the "
            "canonical SatelliteObservation Store."
        )
    )

    parser.add_argument(
        "--probe",
        type=Path,
        default=DEFAULT_PROBE,
        help=(
            "Path to gee_sentinel1_probe.json "
            "(default: validation/gee_sentinel1_probe.json)"
        ),
    )

    parser.add_argument(
        "--scene-index",
        type=int,
        default=0,
        help=(
            "Saved scene index to import "
            "(default: 0, the newest saved scene)"
        ),
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

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    store = (
        EventStore(args.db)
        if args.db is not None
        else EventStore()
    )

    try:
        result = import_probe_file(
            store,
            args.probe,
            scene_index=args.scene_index,
        )
    except GeeProbeImportError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
