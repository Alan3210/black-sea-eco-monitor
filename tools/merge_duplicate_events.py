import argparse
import shutil
import sqlite3
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path("database/events.db")

STATUS_ORDER = {
    "detected": 0,
    "active": 1,
    "contained": 2,
    "resolved": 3,
}

SEVERITY_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def fetch_events(connection):
    rows = connection.execute(
        """
        SELECT
            id,
            category,
            location_name,
            primary_title,
            status,
            severity,
            confidence,
            first_seen,
            last_seen,
            created_at,
            updated_at
        FROM events
        """
    ).fetchall()

    return {
        row[0]: {
            "id": row[0],
            "category": row[1],
            "location_name": row[2],
            "primary_title": row[3],
            "status": row[4],
            "severity": row[5],
            "confidence": row[6],
            "first_seen": row[7],
            "last_seen": row[8],
            "created_at": row[9],
            "updated_at": row[10],
        }
        for row in rows
    }


def build_duplicate_components(connection):
    duplicate_urls = connection.execute(
        """
        SELECT url
        FROM event_evidence
        WHERE url IS NOT NULL
          AND length(trim(url)) > 0
        GROUP BY url
        HAVING COUNT(DISTINCT event_id) > 1
        """
    ).fetchall()

    graph = defaultdict(set)

    for (url,) in duplicate_urls:
        event_ids = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT event_id
                FROM event_evidence
                WHERE url = ?
                """,
                (url,),
            ).fetchall()
        ]

        for event_id in event_ids:
            for other_id in event_ids:
                if event_id != other_id:
                    graph[event_id].add(other_id)

    components = []
    visited = set()

    for start in sorted(graph):
        if start in visited:
            continue

        queue = deque([start])
        visited.add(start)
        component = []

        while queue:
            current = queue.popleft()
            component.append(current)

            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if len(component) > 1:
            components.append(
                sorted(component)
            )

    return components


def evidence_count(connection, event_id):
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM event_evidence
        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()[0]


def choose_canonical_event(component, events):
    # Preserve the oldest event identity.
    # This keeps the ID that first represented
    # the real-world incident in the store.
    return min(
        component,
        key=lambda event_id: (
            events[event_id]["first_seen"] or "",
            events[event_id]["created_at"] or "",
            event_id,
        ),
    )


def choose_advanced_status(component, events):
    return max(
        (
            events[event_id]["status"]
            for event_id in component
        ),
        key=lambda status: STATUS_ORDER.get(
            status,
            -1,
        ),
    )


def choose_highest_severity(component, events):
    severities = [
        events[event_id]["severity"]
        for event_id in component
        if events[event_id]["severity"]
    ]

    if not severities:
        return None

    return max(
        severities,
        key=lambda severity: SEVERITY_ORDER.get(
            severity,
            -1,
        ),
    )


def find_duplicate_evidence_on_target(
    connection,
    *,
    target_event_id,
    source,
    title,
    url,
):
    if url and url.strip():
        return connection.execute(
            """
            SELECT id
            FROM event_evidence
            WHERE event_id = ?
              AND url = ?
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (
                target_event_id,
                url.strip(),
            ),
        ).fetchone()

    return connection.execute(
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
        ORDER BY created_at ASC, id ASC
        LIMIT 1
        """,
        (
            target_event_id,
            source,
            title,
        ),
    ).fetchone()


def merge_source_into_target(
    connection,
    *,
    source_event_id,
    target_event_id,
):
    moved = 0
    removed_duplicates = 0

    evidence_rows = connection.execute(
        """
        SELECT
            id,
            source,
            title,
            url
        FROM event_evidence
        WHERE event_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (source_event_id,),
    ).fetchall()

    for (
        evidence_id,
        source,
        title,
        url,
    ) in evidence_rows:
        duplicate = find_duplicate_evidence_on_target(
            connection,
            target_event_id=target_event_id,
            source=source,
            title=title,
            url=url,
        )

        if duplicate:
            target_evidence_id = duplicate[0]

            connection.execute(
                """
                UPDATE event_status_history
                SET evidence_id = ?
                WHERE evidence_id = ?
                """,
                (
                    target_evidence_id,
                    evidence_id,
                ),
            )

            connection.execute(
                """
                DELETE FROM event_evidence
                WHERE id = ?
                """,
                (evidence_id,),
            )

            removed_duplicates += 1

        else:
            connection.execute(
                """
                UPDATE event_evidence
                SET event_id = ?
                WHERE id = ?
                """,
                (
                    target_event_id,
                    evidence_id,
                ),
            )

            moved += 1

    connection.execute(
        """
        UPDATE event_status_history
        SET event_id = ?
        WHERE event_id = ?
        """,
        (
            target_event_id,
            source_event_id,
        ),
    )

    connection.execute(
        """
        DELETE FROM events
        WHERE id = ?
        """,
        (source_event_id,),
    )

    return moved, removed_duplicates


def merge_component(
    connection,
    *,
    component,
    events,
):
    target_event_id = choose_canonical_event(
        component,
        events,
    )

    status = choose_advanced_status(
        component,
        events,
    )

    severity = choose_highest_severity(
        component,
        events,
    )

    confidence = max(
        (
            events[event_id]["confidence"] or 0.0
            for event_id in component
        ),
        default=0.0,
    )

    first_seen = min(
        (
            events[event_id]["first_seen"]
            for event_id in component
            if events[event_id]["first_seen"]
        ),
        default=events[target_event_id]["first_seen"],
    )

    last_seen = max(
        (
            events[event_id]["last_seen"]
            for event_id in component
            if events[event_id]["last_seen"]
        ),
        default=events[target_event_id]["last_seen"],
    )

    moved = 0
    removed_duplicates = 0

    for source_event_id in component:
        if source_event_id == target_event_id:
            continue

        source_moved, source_removed = (
            merge_source_into_target(
                connection,
                source_event_id=source_event_id,
                target_event_id=target_event_id,
            )
        )

        moved += source_moved
        removed_duplicates += source_removed

    now = datetime.now(
        timezone.utc
    ).isoformat()

    connection.execute(
        """
        UPDATE events
        SET
            status = ?,
            severity = ?,
            confidence = ?,
            first_seen = ?,
            last_seen = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            severity,
            confidence,
            first_seen,
            last_seen,
            now,
            target_event_id,
        ),
    )

    return {
        "target_event_id": target_event_id,
        "moved": moved,
        "removed_duplicates": (
            removed_duplicates
        ),
    }


def print_plan(
    connection,
    *,
    components,
    events,
):
    print(
        "Duplicate event groups:",
        len(components),
    )
    print()

    mergeable = []

    for index, component in enumerate(
        components,
        start=1,
    ):
        categories = {
            events[event_id]["category"]
            for event_id in component
        }

        locations = {
            events[event_id]["location_name"]
            for event_id in component
        }

        target = choose_canonical_event(
            component,
            events,
        )

        safe = (
            len(categories) == 1
            and len(locations) == 1
        )

        print("=" * 88)
        print(
            f"Group #{index}: "
            f"{len(component)} events"
        )
        print(
            "Safe automatic merge:",
            safe,
        )
        print(
            "Canonical event:",
            target,
        )
        print()

        for event_id in component:
            event = events[event_id]

            print(
                f"  {event_id}"
            )
            print(
                f"    {event['category']} | "
                f"{event['location_name']} | "
                f"{event['status']}"
            )
            print(
                f"    Evidence: "
                f"{evidence_count(connection, event_id)}"
            )
            print(
                f"    First seen: "
                f"{event['first_seen']}"
            )
            print(
                f"    Primary title: "
                f"{event['primary_title']}"
            )
            print()

        if safe:
            mergeable.append(component)

    return mergeable


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Safely merge duplicate events that "
            "share identical evidence URLs."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply merges. Without this flag "
            "the script only prints a dry-run."
        ),
    )

    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )

    events = fetch_events(
        connection
    )

    components = build_duplicate_components(
        connection
    )

    mergeable = print_plan(
        connection,
        components=components,
        events=events,
    )

    print()
    print("=" * 88)

    if not args.apply:
        print(
            "DRY RUN ONLY — database was not changed."
        )
        print(
            "Mergeable groups:",
            len(mergeable),
        )
        print(
            "Run with --apply only after reviewing "
            "the plan."
        )
        connection.close()
        return

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = DB_PATH.with_name(
        "events_backup_before_event_merge_"
        f"{timestamp}.db"
    )

    connection.close()

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
        events = fetch_events(
            connection
        )

        connection.execute(
            "BEGIN"
        )

        total_moved = 0
        total_removed = 0
        merged_groups = 0

        for component in mergeable:
            # Refresh existing IDs in case a previous
            # component changed the database.
            existing_component = [
                event_id
                for event_id in component
                if connection.execute(
                    """
                    SELECT 1
                    FROM events
                    WHERE id = ?
                    """,
                    (event_id,),
                ).fetchone()
            ]

            if len(existing_component) < 2:
                continue

            result = merge_component(
                connection,
                component=existing_component,
                events=events,
            )

            merged_groups += 1
            total_moved += result["moved"]
            total_removed += (
                result["removed_duplicates"]
            )

            print(
                "Merged group into:",
                result["target_event_id"],
            )

        connection.commit()

        remaining_cross_event_urls = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT url
                    FROM event_evidence
                    WHERE url IS NOT NULL
                      AND length(trim(url)) > 0
                    GROUP BY url
                    HAVING COUNT(DISTINCT event_id) > 1
                )
                """
            ).fetchone()[0]
        )

        print()
        print(
            "Merged groups:",
            merged_groups,
        )
        print(
            "Evidence moved:",
            total_moved,
        )
        print(
            "Duplicate evidence rows removed:",
            total_removed,
        )
        print(
            "Remaining cross-event duplicate URLs:",
            remaining_cross_event_urls,
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
