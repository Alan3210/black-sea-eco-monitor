import sqlite3
from pathlib import Path


DB_PATH = Path("database/events.db")


def format_coordinate(value):
    if value is None:
        return "NULL"

    return f"{value:.6f}"


def main():
    if not DB_PATH.exists():
        raise SystemExit(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )

    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(events)"
        ).fetchall()
    }

    print("EVENT STORE COORDINATE CHECK")
    print()

    print(
        "latitude column:",
        "OK" if "latitude" in columns else "MISSING",
    )
    print(
        "longitude column:",
        "OK" if "longitude" in columns else "MISSING",
    )
    print()

    if (
        "latitude" not in columns
        or "longitude" not in columns
    ):
        connection.close()
        return

    rows = connection.execute(
        """
        SELECT
            e.id,
            e.category,
            e.location_name,
            e.status,
            e.latitude,
            e.longitude,
            COUNT(ev.id) AS evidence_count
        FROM events AS e
        LEFT JOIN event_evidence AS ev
            ON ev.event_id = e.id
        GROUP BY
            e.id,
            e.category,
            e.location_name,
            e.status,
            e.latitude,
            e.longitude
        ORDER BY
            e.location_name,
            e.category,
            e.created_at
        """
    ).fetchall()

    total = len(rows)

    with_coordinates = sum(
        1
        for row in rows
        if row[4] is not None
        and row[5] is not None
    )

    missing_coordinates = (
        total - with_coordinates
    )

    print(f"Events total: {total}")
    print(
        "Events with coordinates:",
        with_coordinates,
    )
    print(
        "Events without coordinates:",
        missing_coordinates,
    )
    print()

    for (
        event_id,
        category,
        location_name,
        status,
        latitude,
        longitude,
        evidence_count,
    ) in rows:
        print("=" * 88)
        print(f"Event ID: {event_id}")
        print(f"Category: {category}")
        print(f"Location: {location_name}")
        print(f"Status: {status}")
        print(f"Evidence: {evidence_count}")
        print(
            "Latitude:",
            format_coordinate(latitude),
        )
        print(
            "Longitude:",
            format_coordinate(longitude),
        )

    connection.close()


if __name__ == "__main__":
    main()
