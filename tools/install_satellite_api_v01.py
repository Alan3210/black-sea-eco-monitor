from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = REPO_ROOT / "backend" / "main.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

IMPORT_BLOCK = """from backend.api.satellite_observations import (
    router as satellite_observations_router,
)

"""

ROUTER_BLOCK = """
app.include_router(
    satellite_observations_router,
    prefix="/satellite/observations",
    tags=["satellite"],
)


"""


def main() -> int:
    if not MAIN_PATH.exists():
        print(f"ERROR: target not found: {MAIN_PATH}")
        return 2

    text = MAIN_PATH.read_text(encoding="utf-8")

    import_present = (
        "satellite_observations_router" in text
        and "backend.api.satellite_observations" in text
    )
    router_present = (
        'prefix="/satellite/observations"' in text
    )

    if import_present and router_present:
        print(
            "SAT-4 Satellite API v0.1 already wired into "
            "backend/main.py; no edit applied."
        )
        return 0

    import_marker = (
        "from backend.database.database import engine, Base"
    )
    router_marker = '@app.get("/")'

    if not import_present and import_marker not in text:
        print(
            "ERROR: import insertion marker not found in "
            "backend/main.py. No changes were made."
        )
        return 3

    if not router_present and router_marker not in text:
        print(
            "ERROR: router insertion marker not found in "
            "backend/main.py. No changes were made."
        )
        return 4

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    backup = (
        BACKUP_DIR
        / f"main.before_sat4_api_v01_{stamp}.py"
    )
    shutil.copy2(
        MAIN_PATH,
        backup,
    )

    updated = text

    if not import_present:
        updated = updated.replace(
            import_marker,
            IMPORT_BLOCK + import_marker,
            1,
        )

    if not router_present:
        updated = updated.replace(
            router_marker,
            ROUTER_BLOCK + router_marker,
            1,
        )

    MAIN_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print("SAT-4 Satellite API v0.1 installed.")
    print(
        "Modified: "
        f"{MAIN_PATH.relative_to(REPO_ROOT)}"
    )
    print(
        "Router: backend\\api\\"
        "satellite_observations.py"
    )
    print(
        "Backup: "
        f"{backup.relative_to(REPO_ROOT)}"
    )
    print(
        "Run syntax and targeted tests before committing."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
