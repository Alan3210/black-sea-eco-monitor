import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "database" / "events.db"
BACKUP_DIR = REPO_ROOT / "database" / "backups"

FALSE_POSITIVE_TITLE = (
    "Разлив нефти в Керченском проливе: "
    "суд принял уточненный иск к судовладельцам - BFM Кубань"
)

EXPECTED_CATEGORY = "oil_spill"
EXPECTED_LOCATION = "Kerch Strait"


def find_false_positive(connection):
    rows = connection.execute(
        """
        SELECT
            id,
            category,
            location_name,
            primary_title
        FROM events
        WHERE primary_title = ?
        """,
        (FALSE_POSITIVE_TITLE,),
    ).fetchall()

    if not rows:
        return None

    if len(rows) != 1:
        raise RuntimeError(
            "Cleanup aborted: expected at most one exact "
            "false-positive event."
        )

    row = rows[0]

    if (
        row[1] != EXPECTED_CATEGORY
        or row[2] != EXPECTED_LOCATION
    ):
        raise RuntimeError(
            "Cleanup aborted: exact title matched, but category "
            "or location did not match the expected false positive."
        )

    return row


def create_backup():
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / f"events_before_data_quality_v11_{stamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    return backup_path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Backfill legacy detection_time and remove the "
            "known Kerch Strait legal-news false positive."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply changes. Without this flag the script "
            "only performs a dry run."
        ),
    )

    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}"
        )

    with sqlite3.connect(DB_PATH) as connection:
        missing_detection = connection.execute(
            """
            SELECT COUNT(*)
            FROM events
            WHERE detection_time IS NULL
            """
        ).fetchone()[0]

        false_positive = find_false_positive(
            connection
        )

        print("DATA QUALITY V1.1 CLEANUP")
        print(f"Database: {DB_PATH}")
        print(
            "Legacy events missing detection_time: "
            f"{missing_detection}"
        )

        if false_positive:
            print(
                "False-positive event found: "
                f"{false_positive[0]}"
            )
            print(
                f"  {false_positive[3]}"
            )
        else:
            print(
                "False-positive event: not present."
            )

        if not args.apply:
            print()
            print(
                "DRY RUN ONLY — no database changes made."
            )
            print(
                "Run again with --apply after reviewing "
                "the output."
            )
            return

        backup_path = create_backup()

        print()
        print(
            f"Backup created: {backup_path}"
        )

        connection.execute(
            """
            UPDATE events
            SET detection_time = created_at
            WHERE detection_time IS NULL
            """
        )

        backfilled = connection.execute(
            "SELECT changes()"
        ).fetchone()[0]

        deleted_event = 0

        if false_positive:
            event_id = false_positive[0]

            connection.execute(
                """
                DELETE FROM event_status_history
                WHERE event_id = ?
                """,
                (event_id,),
            )

            connection.execute(
                """
                DELETE FROM event_evidence
                WHERE event_id = ?
                """,
                (event_id,),
            )

            connection.execute(
                """
                DELETE FROM events
                WHERE id = ?
                """,
                (event_id,),
            )

            deleted_event = connection.execute(
                "SELECT changes()"
            ).fetchone()[0]

        connection.commit()

    print()
    print(
        "Applied detection_time backfill: "
        f"{backfilled} event(s)"
    )
    print(
        "Deleted known false-positive event: "
        f"{deleted_event}"
    )
    print("SUCCESS")


if __name__ == "__main__":
    main()
