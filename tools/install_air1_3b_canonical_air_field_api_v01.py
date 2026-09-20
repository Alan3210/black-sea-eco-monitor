from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = REPO_ROOT / "backend" / "main.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

IMPORT_LINE = (
    "from backend.api.air_field "
    "import router as air_field_router"
)

WIND_IMPORT = (
    "from backend.api.wind_field "
    "import router as wind_field_router"
)

INCLUDE_LINE = (
    "app.include_router(air_field_router)"
)


def main() -> int:
    if not MAIN_PATH.exists():
        print(
            "ERROR: backend/main.py not found."
        )
        return 2

    text = MAIN_PATH.read_text(
        encoding="utf-8",
    )

    if (
        IMPORT_LINE in text
        and INCLUDE_LINE in text
    ):
        print(
            "AIR-1.3B Canonical Air Field API v0.1 already installed."
        )
        return 0

    if (
        IMPORT_LINE not in text
        and WIND_IMPORT not in text
    ):
        print(
            "ERROR: wind_field import anchor not found."
        )
        print(
            "No tracked files modified."
        )
        return 3

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup = (
        BACKUP_DIR
        / (
            "backend_main.py"
            f".before_air1_3b_{stamp}"
        )
    )

    shutil.copy2(
        MAIN_PATH,
        backup,
    )

    updated = text

    if IMPORT_LINE not in updated:
        updated = updated.replace(
            WIND_IMPORT,
            (
                f"{WIND_IMPORT}\n"
                f"{IMPORT_LINE}"
            ),
            1,
        )

    if INCLUDE_LINE not in updated:
        updated = (
            updated.rstrip()
            + "\n\n"
            + INCLUDE_LINE
            + "\n"
        )

    try:
        MAIN_PATH.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )
    except Exception:
        shutil.copy2(
            backup,
            MAIN_PATH,
        )
        raise

    print(
        "AIR-1.3B Canonical Air Field API v0.1 installed."
    )
    print(
        "Registered: GET /air/field"
    )
    print(
        "Canonical semantics: CAMS model forecast, not station observation."
    )
    print(
        "Uses existing CAMS cache when it contains the requested run/pollutant/lead."
    )
    print(
        "Downloads a matching CAMS field on cache miss."
    )
    print(
        "No Web GIS, GEOS-CF, Sentinel-5P, FIRMS, Impact or OpenDrift code modified."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
