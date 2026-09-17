from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
EVENT_STORE_PATH = (
    REPO_ROOT / "agents" / "news_agent" / "event_store.py"
)
MONITOR_API_PATH = (
    REPO_ROOT / "backend" / "api" / "monitor_events.py"
)
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

EVENT_STORE_METHOD = '    def get_event_satellite_observations(\n        self,\n        event_id,\n    ):\n        with self._connect() as connection:\n            rows = connection.execute(\n                """\n                SELECT\n                    satellite_observation_id,\n                    relation_type,\n                    relation_confidence,\n                    created_at\n                FROM event_satellite_observations\n                WHERE event_id = ?\n                ORDER BY created_at ASC\n                """,\n                (event_id,),\n            ).fetchall()\n\n        records = []\n\n        for (\n            satellite_observation_id,\n            relation_type,\n            relation_confidence,\n            created_at,\n        ) in rows:\n            observation = self.get_satellite_observation(\n                satellite_observation_id\n            )\n\n            if observation is None:\n                continue\n\n            records.append(\n                {\n                    "relation_type": relation_type,\n                    "relation_confidence": (\n                        relation_confidence\n                    ),\n                    "created_at": created_at,\n                    "observation": observation,\n                }\n            )\n\n        return records\n\n'
API_ENDPOINT = '@router.get("/{event_id}/satellite-observations")\ndef get_monitor_event_satellite_observations(\n    event_id: str,\n    store: EventStore = Depends(\n        get_monitor_event_store\n    ),\n):\n    event = store.get_event_record(\n        event_id\n    )\n\n    if event is None:\n        raise HTTPException(\n            status_code=404,\n            detail="Event not found",\n        )\n\n    return store.get_event_satellite_observations(\n        event_id\n    )\n\n\n'

EVENT_STORE_MARKER = (
    "\n    def get_event_evidence(self, event_id):\n"
)
API_MARKER = (
    '@router.get("/{event_id}/evidence")\n'
)


def _backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = (
        BACKUP_DIR
        / f"{label}.before_sat6_read_v01_{stamp}.py"
    )
    shutil.copy2(path, backup)
    return backup


def main() -> int:
    for path in (
        EVENT_STORE_PATH,
        MONITOR_API_PATH,
    ):
        if not path.exists():
            print(f"ERROR: target not found: {path}")
            return 2

    store_text = EVENT_STORE_PATH.read_text(
        encoding="utf-8"
    )
    api_text = MONITOR_API_PATH.read_text(
        encoding="utf-8"
    )

    store_present = (
        "    def get_event_satellite_observations(" in store_text
    )
    api_present = (
        '@router.get("/{event_id}/satellite-observations")'
        in api_text
    )

    if store_present and api_present:
        print(
            "SAT-6 event-satellite read side v0.1 "
            "already installed; no edit applied."
        )
        return 0

    if (
        not store_present
        and EVENT_STORE_MARKER not in store_text
    ):
        print(
            "ERROR: EventStore insertion marker not found. "
            "No changes were made."
        )
        return 3

    if (
        not api_present
        and API_MARKER not in api_text
    ):
        print(
            "ERROR: monitor API insertion marker not found. "
            "No changes were made."
        )
        return 4

    store_backup = _backup(
        EVENT_STORE_PATH,
        "event_store",
    )
    api_backup = _backup(
        MONITOR_API_PATH,
        "monitor_events",
    )

    if not store_present:
        store_text = store_text.replace(
            EVENT_STORE_MARKER,
            "\n" + EVENT_STORE_METHOD + EVENT_STORE_MARKER,
            1,
        )
        EVENT_STORE_PATH.write_text(
            store_text,
            encoding="utf-8",
        )

    if not api_present:
        api_text = api_text.replace(
            API_MARKER,
            API_ENDPOINT + API_MARKER,
            1,
        )
        MONITOR_API_PATH.write_text(
            api_text,
            encoding="utf-8",
        )

    print(
        "SAT-6 event-satellite read side v0.1 installed."
    )
    print(
        "Modified: agents\\news_agent\\event_store.py"
    )
    print(
        "Modified: backend\\api\\monitor_events.py"
    )
    print(
        "Backup: "
        f"{store_backup.relative_to(REPO_ROOT)}"
    )
    print(
        "Backup: "
        f"{api_backup.relative_to(REPO_ROOT)}"
    )
    print(
        "Run syntax and targeted tests before committing."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
