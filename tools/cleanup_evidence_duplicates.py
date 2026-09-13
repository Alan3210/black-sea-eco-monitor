import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path("database/events.db")


def main():
    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}"
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = DB_PATH.with_name(
        f"events_backup_before_evidence_cleanup_{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path,
    )

    print(
        f"Backup created: {backup_path}"
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    try:
        before_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM event_evidence
            """
        ).fetchone()[0]

        duplicate_url_groups = (
            connection.execute(
                """
                SELECT
                    event_id,
                    url,
                    COUNT(*)
                FROM event_evidence
                WHERE url IS NOT NULL
                  AND length(trim(url)) > 0
                GROUP BY event_id, url
                HAVING COUNT(*) > 1
                """
            ).fetchall()
        )

        duplicate_no_url_groups = (
            connection.execute(
                """
                SELECT
                    event_id,
                    source,
                    title,
                    COUNT(*)
                FROM event_evidence
                WHERE url IS NULL
                   OR length(trim(url)) = 0
                GROUP BY
                    event_id,
                    source,
                    title
                HAVING COUNT(*) > 1
                """
            ).fetchall()
        )

        removed = 0

        connection.execute(
            "BEGIN"
        )

        for (
            event_id,
            url,
            count,
        ) in duplicate_url_groups:

            rows = connection.execute(
                """
                SELECT id
                FROM event_evidence
                WHERE event_id = ?
                  AND url = ?
                ORDER BY
                    created_at ASC,
                    id ASC
                """,
                (
                    event_id,
                    url,
                ),
            ).fetchall()

            duplicate_ids = [
                row[0]
                for row in rows[1:]
            ]

            for evidence_id in duplicate_ids:
                connection.execute(
                    """
                    DELETE FROM event_evidence
                    WHERE id = ?
                    """,
                    (evidence_id,),
                )

            removed += len(
                duplicate_ids
            )

        for (
            event_id,
            source,
            title,
            count,
        ) in duplicate_no_url_groups:

            rows = connection.execute(
                """
                SELECT id
                FROM event_evidence
                WHERE event_id = ?
                  AND source IS ?
                  AND title IS ?
                  AND (
                      url IS NULL
                      OR length(trim(url)) = 0
                  )
                ORDER BY
                    created_at ASC,
                    id ASC
                """,
                (
                    event_id,
                    source,
                    title,
                ),
            ).fetchall()

            duplicate_ids = [
                row[0]
                for row in rows[1:]
            ]

            for evidence_id in duplicate_ids:
                connection.execute(
                    """
                    DELETE FROM event_evidence
                    WHERE id = ?
                    """,
                    (evidence_id,),
                )

            removed += len(
                duplicate_ids
            )

        connection.commit()

        after_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM event_evidence
            """
        ).fetchone()[0]

        print(
            "Duplicate URL groups "
            f"inside same event: "
            f"{len(duplicate_url_groups)}"
        )

        print(
            "Duplicate no-URL groups "
            f"inside same event: "
            f"{len(duplicate_no_url_groups)}"
        )

        print(
            f"Evidence before: "
            f"{before_count}"
        )

        print(
            f"Evidence removed: "
            f"{removed}"
        )

        print(
            f"Evidence after: "
            f"{after_count}"
        )

        print()
        print(
            "Cross-event duplicates were "
            "NOT modified."
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
