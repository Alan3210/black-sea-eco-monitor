import sqlite3
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "events.db"
)

EXPECTED_COLUMNS = [
    "location_type",
    "location_confidence",
    "coordinate_source",
    "incident_time",
    "detection_time",
    "source_time",
]


def main():
    print(f"Database: {DB_PATH}")

    if not DB_PATH.exists():
        raise SystemExit("ERROR: database/events.db was not found.")

    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "PRAGMA table_info(events)"
        ).fetchall()

    columns = [row[1] for row in rows]

    print("\nEvent columns:")
    for column in columns:
        print(f"  - {column}")

    print("\nData Quality v1 columns:")
    missing = []

    for column in EXPECTED_COLUMNS:
        if column in columns:
            print(f"  [OK] {column}")
        else:
            print(f"  [MISSING] {column}")
            missing.append(column)

    if missing:
        raise SystemExit(
            "\nERROR: migration is incomplete."
        )

    print("\nSUCCESS: Event Store schema migration is complete.")


if __name__ == "__main__":
    main()
