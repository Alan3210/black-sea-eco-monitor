from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "backend" / "api" / "monitor_events.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

IMPORT_BLOCK = """from backend.services.monitor_context import (
    build_monitor_event_context,
)

"""

ENDPOINT_BLOCK = '@router.get("/{event_id}/context")\ndef get_monitor_event_context(\n    event_id: str,\n    store: EventStore = Depends(\n        get_monitor_event_store\n    ),\n):\n    context = build_monitor_event_context(\n        store,\n        event_id,\n    )\n\n    if context is None:\n        raise HTTPException(\n            status_code=404,\n            detail="Event not found",\n        )\n\n    return context\n\n\n'

IMPORT_MARKER = """from agents.news_agent.event_store import (
    EventStore,
)


"""

ENDPOINT_MARKER = (
    '@router.get("/{event_id}/satellite-observations")\n'
)


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: target not found: {TARGET}")
        return 2

    text = TARGET.read_text(encoding="utf-8")

    import_present = (
        "build_monitor_event_context" in text
        and "backend.services.monitor_context" in text
    )
    endpoint_present = (
        '@router.get("/{event_id}/context")' in text
    )

    if import_present and endpoint_present:
        print(
            "SYSTEM-1 monitor context endpoint "
            "already installed; no edit applied."
        )
        return 0

    if not import_present and IMPORT_MARKER not in text:
        print(
            "ERROR: import insertion marker not found. "
            "No changes were made."
        )
        return 3

    if not endpoint_present and ENDPOINT_MARKER not in text:
        print(
            "ERROR: endpoint insertion marker not found. "
            "No changes were made."
        )
        return 4

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = (
        BACKUP_DIR
        / f"monitor_events.before_system1_context_{stamp}.py"
    )
    shutil.copy2(TARGET, backup)

    updated = text

    if not import_present:
        updated = updated.replace(
            IMPORT_MARKER,
            IMPORT_MARKER + IMPORT_BLOCK,
            1,
        )

    if not endpoint_present:
        updated = updated.replace(
            ENDPOINT_MARKER,
            ENDPOINT_BLOCK + ENDPOINT_MARKER,
            1,
        )

    TARGET.write_text(
        updated,
        encoding="utf-8",
    )

    print("SYSTEM-1 monitor context endpoint installed.")
    print("Modified: backend\\api\\monitor_events.py")
    print("Service: backend\\services\\monitor_context.py")
    print(
        "Backup: "
        f"{backup.relative_to(REPO_ROOT)}"
    )
    print(
        "Added: GET /monitor/events/{event_id}/context"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
