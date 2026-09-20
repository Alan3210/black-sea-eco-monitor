
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / ".air1_3c9_1_payload" / "frontend/src"

FILES = (
    "camsAirOperationalField.js",
    "camsAirOperationalField.test.js",
)


def main() -> int:
    target_dir = ROOT / "frontend/src"

    for name in FILES:
        if not (PAYLOAD / name).exists():
            print(f"ERROR: missing payload: {name}")
            return 2

        if not (target_dir / name).exists():
            print(f"ERROR: target missing: frontend/src/{name}")
            return 3

    current = (
        target_dir
        / "camsAirOperationalField.js"
    ).read_text(
        encoding="utf-8"
    )

    if "camsRobustFieldStops" in current:
        print(
            "AIR-1.3C.9.1 Robust CAMS Color Scale + Opacity Fix v0.1 already installed."
        )
        return 0

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup_root = (
        ROOT
        / "dev-snapshots"
        / f"air1_3c9_1_before_apply_{stamp}"
        / "frontend/src"
    )

    backup_root.mkdir(
        parents=True,
        exist_ok=False,
    )

    for name in FILES:
        shutil.copy2(
            target_dir / name,
            backup_root / name,
        )

    try:
        for name in FILES:
            shutil.copy2(
                PAYLOAD / name,
                target_dir / name,
            )

        final = (
            target_dir
            / "camsAirOperationalField.js"
        ).read_text(
            encoding="utf-8"
        )

        for marker in (
            "value === null",
            "camsPercentile",
            "camsRobustFieldStops",
        ):
            if marker not in final:
                raise RuntimeError(
                    f"verification failed: {marker}"
                )

    except Exception:
        for name in FILES:
            shutil.copy2(
                backup_root / name,
                target_dir / name,
            )
        raise

    shutil.rmtree(
        ROOT / ".air1_3c9_1_payload"
    )

    print(
        "AIR-1.3C.9.1 Robust CAMS Color Scale + Opacity Fix v0.1 installed."
    )
    print(
        "Default opacity: missing storage value -> 55%"
    )
    print(
        "Color scale: robust P5/P25/P50/P75/P95"
    )
    print(
        "MIN/MEAN/MAX remain actual field statistics"
    )
    print(
        "Popup remains exact model concentration"
    )
    print(
        "Backup:"
    )
    print(
        backup_root.parent.parent
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
