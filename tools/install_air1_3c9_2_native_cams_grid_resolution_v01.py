
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "frontend/src/main.js"

OLD = (
    "`${CAMS_RUNTIME_CONFIG.endpoint}"
    "?pollutant=${camsAirPollutant}&stride=2`,"
)

NEW = (
    "`${CAMS_RUNTIME_CONFIG.endpoint}"
    "?pollutant=${camsAirPollutant}&stride=1`,"
)


def main() -> int:
    if not MAIN.exists():
        print("ERROR: frontend/src/main.js not found.")
        return 2

    text = MAIN.read_text(
        encoding="utf-8",
    )

    if NEW in text:
        print(
            "AIR-1.3C.9.2 Native CAMS Grid Resolution v0.1 already installed."
        )
        return 0

    count = text.count(OLD)

    if count != 1:
        print(
            f"ERROR: expected one CAMS stride=2 anchor, found {count}."
        )
        print(
            "No files modified."
        )
        return 3

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup = (
        ROOT
        / "dev-snapshots"
        / f"air1_3c9_2_before_native_grid_{stamp}"
        / "frontend/src/main.js"
    )

    backup.parent.mkdir(
        parents=True,
        exist_ok=False,
    )

    shutil.copy2(
        MAIN,
        backup,
    )

    updated = text.replace(
        OLD,
        NEW,
        1,
    )

    MAIN.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    verify = MAIN.read_text(
        encoding="utf-8",
    )

    if NEW not in verify:
        shutil.copy2(
            backup,
            MAIN,
        )
        print(
            "ERROR: native CAMS grid verification failed; backup restored."
        )
        return 4

    print(
        "AIR-1.3C.9.2 Native CAMS Grid Resolution v0.1 installed."
    )
    print(
        "CAMS frontend request stride: 2 -> 1"
    )
    print(
        "Expected grid: ~45x88 -> ~90x175"
    )
    print(
        "Expected cell width/height: approximately halved"
    )
    print(
        "No synthetic upscaling or interpolation added."
    )
    print(
        "Backup:"
    )
    print(
        backup.parent.parent.parent
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
