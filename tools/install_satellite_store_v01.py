from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "agents" / "news_agent" / "event_store.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

INSERT_MARKER = '            cursor.execute("""\n                CREATE INDEX IF NOT EXISTS\n                idx_event_evidence_event_url\n'
SCHEMA_BLOCK = '\n            cursor.execute("""\n                CREATE TABLE IF NOT EXISTS satellite_observations (\n                    id TEXT PRIMARY KEY,\n\n                    information_type TEXT NOT NULL,\n                    derivation_level TEXT NOT NULL,\n                    observation_type TEXT NOT NULL,\n\n                    sensor TEXT NOT NULL,\n                    platform TEXT,\n                    dataset_id TEXT NOT NULL,\n                    source_image_id TEXT NOT NULL,\n\n                    acquisition_time TEXT NOT NULL,\n                    processing_time TEXT,\n\n                    geometry_geojson TEXT,\n\n                    bbox_min_lon REAL,\n                    bbox_min_lat REAL,\n                    bbox_max_lon REAL,\n                    bbox_max_lat REAL,\n\n                    confidence REAL,\n                    review_status TEXT NOT NULL,\n\n                    processing_version TEXT NOT NULL,\n                    processing_method TEXT,\n\n                    cache_reference TEXT,\n                    provenance_json TEXT,\n\n                    created_at TEXT NOT NULL,\n                    updated_at TEXT NOT NULL\n                )\n            """)\n\n            cursor.execute("""\n                CREATE TABLE IF NOT EXISTS event_satellite_observations (\n                    event_id TEXT NOT NULL,\n                    satellite_observation_id TEXT NOT NULL,\n\n                    relation_type TEXT NOT NULL,\n                    relation_confidence REAL,\n\n                    created_at TEXT NOT NULL,\n\n                    PRIMARY KEY (\n                        event_id,\n                        satellite_observation_id\n                    ),\n\n                    FOREIGN KEY(event_id)\n                        REFERENCES events(id),\n\n                    FOREIGN KEY(satellite_observation_id)\n                        REFERENCES satellite_observations(id)\n                )\n            """)\n\n            cursor.execute("""\n                CREATE INDEX IF NOT EXISTS\n                idx_satellite_observations_acquisition_time\n                ON satellite_observations(acquisition_time)\n            """)\n\n            cursor.execute("""\n                CREATE INDEX IF NOT EXISTS\n                idx_satellite_observations_type\n                ON satellite_observations(observation_type)\n            """)\n\n            cursor.execute("""\n                CREATE INDEX IF NOT EXISTS\n                idx_satellite_observations_dataset\n                ON satellite_observations(dataset_id)\n            """)\n\n            cursor.execute("""\n                CREATE INDEX IF NOT EXISTS\n                idx_satellite_observations_source_image\n                ON satellite_observations(source_image_id)\n            """)\n\n            cursor.execute("""\n                CREATE INDEX IF NOT EXISTS\n                idx_satellite_observations_review_status\n                ON satellite_observations(review_status)\n            """)\n\n            cursor.execute("""\n                CREATE INDEX IF NOT EXISTS\n                idx_event_satellite_event\n                ON event_satellite_observations(event_id)\n            """)\n\n'


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: target not found: {TARGET}")
        return 2

    text = TARGET.read_text(encoding="utf-8")

    if "CREATE TABLE IF NOT EXISTS satellite_observations" in text:
        print("SatelliteObservation schema already present; no edit applied.")
        return 0

    if INSERT_MARKER not in text:
        print(
            "ERROR: safe insertion marker was not found in event_store.py. "
            "No changes were made."
        )
        return 3

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"event_store.before_satellite_store_v01_{stamp}.py"
    shutil.copy2(TARGET, backup)

    updated = text.replace(
        INSERT_MARKER,
        SCHEMA_BLOCK + INSERT_MARKER,
        1,
    )

    TARGET.write_text(updated, encoding="utf-8")

    print("SatelliteObservation Store v0.1 schema installed.")
    print(f"Modified: {TARGET.relative_to(REPO_ROOT)}")
    print(f"Backup: {backup.relative_to(REPO_ROOT)}")
    print("Run targeted tests before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
