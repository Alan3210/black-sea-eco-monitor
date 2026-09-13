import sqlite3

from agents.news_agent.event_store import EventStore


def test_create_event_stores_coordinates(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Test wildfire",
        confidence=0.8,
        latitude=44.7240,
        longitude=37.7691,
    )

    assert store.get_event_coordinates(
        event_id
    ) == (
        44.7240,
        37.7691,
    )


def test_set_event_coordinates_backfills_missing_values(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Utrish Reserve",
        primary_title="Test wildfire",
        confidence=0.8,
    )

    assert store.get_event_coordinates(
        event_id
    ) == (
        None,
        None,
    )

    changed = store.set_event_coordinates(
        event_id=event_id,
        latitude=44.7605,
        longitude=37.3854,
    )

    assert changed is True

    assert store.get_event_coordinates(
        event_id
    ) == (
        44.7605,
        37.3854,
    )


def test_existing_events_table_is_migrated_without_deleting_data(
    tmp_path,
):
    db_path = tmp_path / "events.db"

    connection = sqlite3.connect(
        db_path
    )

    connection.execute(
        """
        CREATE TABLE events (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            location_name TEXT NOT NULL,
            primary_title TEXT NOT NULL,
            status TEXT NOT NULL,
            severity TEXT,
            confidence REAL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        INSERT INTO events (
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
        )
        VALUES (
            'evt_existing',
            'wildfire',
            'Novorossiysk',
            'Existing event',
            'detected',
            'medium',
            0.8,
            '2026-09-13T00:00:00+00:00',
            '2026-09-13T00:00:00+00:00',
            '2026-09-13T00:00:00+00:00',
            '2026-09-13T00:00:00+00:00'
        )
        """
    )

    connection.commit()
    connection.close()

    store = EventStore(
        db_path
    )

    with sqlite3.connect(
        db_path
    ) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(events)"
            ).fetchall()
        }

        existing_row = connection.execute(
            """
            SELECT id, primary_title
            FROM events
            WHERE id = 'evt_existing'
            """
        ).fetchone()

    assert "latitude" in columns
    assert "longitude" in columns
    assert existing_row == (
        "evt_existing",
        "Existing event",
    )

    assert store.get_event_coordinates(
        "evt_existing"
    ) == (
        None,
        None,
    )
