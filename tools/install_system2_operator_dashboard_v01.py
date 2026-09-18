from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = REPO_ROOT / "backend" / "main.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

IMPORT_BLOCK = """from backend.api.monitor_dashboard import (
    router as monitor_dashboard_router,
)

"""

ROUTER_BLOCK = """
app.include_router(
    monitor_dashboard_router,
    prefix="/monitor/dashboard",
    tags=["monitor"],
)


"""

IMPORT_MARKER = (
    "from backend.database.database import engine, Base"
)
ROUTER_MARKER = '@app.get("/")'


def main() -> int:
    if not MAIN_PATH.exists():
        print(
            f"ERROR: target not found: {MAIN_PATH}"
        )
        return 2

    text = MAIN_PATH.read_text(
        encoding="utf-8"
    )

    import_present = (
        "monitor_dashboard_router" in text
        and "backend.api.monitor_dashboard"
        in text
    )
    router_present = (
        'prefix="/monitor/dashboard"'
        in text
    )

    if import_present and router_present:
        print(
            "SYSTEM-2 operator dashboard API "
            "already installed; no edit applied."
        )
        return 0

    if (
        not import_present
        and IMPORT_MARKER not in text
    ):
        print(
            "ERROR: import insertion marker "
            "not found. No changes were made."
        )
        return 3

    if (
        not router_present
        and ROUTER_MARKER not in text
    ):
        print(
            "ERROR: router insertion marker "
            "not found. No changes were made."
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
        / f"main.before_system2_dashboard_{stamp}.py"
    )

    shutil.copy2(
        MAIN_PATH,
        backup,
    )

    updated = text

    if not import_present:
        updated = updated.replace(
            IMPORT_MARKER,
            IMPORT_BLOCK + IMPORT_MARKER,
            1,
        )

    if not router_present:
        updated = updated.replace(
            ROUTER_MARKER,
            ROUTER_BLOCK + ROUTER_MARKER,
            1,
        )

    MAIN_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        "SYSTEM-2 operator dashboard API installed."
    )
    print(
        "Modified: backend\\main.py"
    )
    print(
        "Router: backend\\api\\monitor_dashboard.py"
    )
    print(
        "Service: backend\\services\\operator_dashboard.py"
    )
    print(
        "Backup: "
        f"{backup.relative_to(REPO_ROOT)}"
    )
    print(
        "Added: GET /monitor/dashboard/events"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
