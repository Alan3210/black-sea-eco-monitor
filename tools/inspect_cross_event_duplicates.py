import sqlite3
from collections import defaultdict, deque
from pathlib import Path


DB_PATH = Path("database/events.db")


def fetch_event(connection, event_id):
    return connection.execute(
        """
        SELECT
            id,
            category,
            location_name,
            primary_title,
            status,
            confidence,
            first_seen,
            last_seen
        FROM events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()


def evidence_count(connection, event_id):
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM event_evidence
        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)

    duplicate_rows = connection.execute(
        """
        SELECT
            url,
            COUNT(DISTINCT event_id)
        FROM event_evidence
        WHERE url IS NOT NULL
          AND length(trim(url)) > 0
        GROUP BY url
        HAVING COUNT(DISTINCT event_id) > 1
        ORDER BY url
        """
    ).fetchall()

    print(
        "URLs shared by different events:",
        len(duplicate_rows),
    )
    print()

    graph = defaultdict(set)
    url_events = {}

    for index, (url, event_count) in enumerate(
        duplicate_rows,
        start=1,
    ):
        event_ids = [
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT event_id
                FROM event_evidence
                WHERE url = ?
                ORDER BY event_id
                """,
                (url,),
            ).fetchall()
        ]

        url_events[url] = event_ids

        for event_id in event_ids:
            for other_id in event_ids:
                if event_id != other_id:
                    graph[event_id].add(other_id)

        evidence_rows = connection.execute(
            """
            SELECT
                event_id,
                source,
                title,
                published_at
            FROM event_evidence
            WHERE url = ?
            ORDER BY created_at ASC
            """,
            (url,),
        ).fetchall()

        print("=" * 88)
        print(
            f"Duplicate URL #{index} "
            f"(events: {event_count})"
        )
        print(url)
        print()

        for (
            event_id,
            source,
            title,
            published_at,
        ) in evidence_rows:
            event = fetch_event(
                connection,
                event_id,
            )

            if event is None:
                print(
                    f"  Missing event: {event_id}"
                )
                continue

            (
                _,
                category,
                location_name,
                primary_title,
                status,
                confidence,
                first_seen,
                last_seen,
            ) = event

            print(
                f"  Event ID: {event_id}"
            )
            print(
                f"    Category: {category}"
            )
            print(
                f"    Location: {location_name}"
            )
            print(
                f"    Status: {status}"
            )
            print(
                f"    Confidence: {confidence}"
            )
            print(
                f"    Evidence count: "
                f"{evidence_count(connection, event_id)}"
            )
            print(
                f"    Primary title: "
                f"{primary_title}"
            )
            print(
                f"    Shared evidence source: "
                f"{source}"
            )
            print(
                f"    Shared evidence title: "
                f"{title}"
            )
            print(
                f"    Shared evidence published: "
                f"{published_at}"
            )
            print(
                f"    First seen: {first_seen}"
            )
            print(
                f"    Last seen: {last_seen}"
            )
            print()

    print()
    print("=" * 88)
    print("CONNECTED EVENT GROUPS")
    print(
        "(events connected because they share "
        "at least one identical evidence URL)"
    )
    print()

    visited = set()
    group_number = 0

    for start_event in sorted(graph):
        if start_event in visited:
            continue

        group_number += 1
        queue = deque([start_event])
        visited.add(start_event)
        component = []

        while queue:
            current = queue.popleft()
            component.append(current)

            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        print(
            f"Group #{group_number}: "
            f"{len(component)} events"
        )

        for event_id in sorted(component):
            event = fetch_event(
                connection,
                event_id,
            )

            if event is None:
                continue

            (
                _,
                category,
                location_name,
                primary_title,
                status,
                confidence,
                first_seen,
                last_seen,
            ) = event

            print(
                f"  {event_id}"
            )
            print(
                f"    {category} | "
                f"{location_name} | "
                f"{status}"
            )
            print(
                f"    {primary_title}"
            )

        print()

    connection.close()


if __name__ == "__main__":
    main()
