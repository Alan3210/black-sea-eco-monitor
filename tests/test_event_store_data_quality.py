import sqlite3

import pytest

from agents.news_agent.event_store import EventStore


NEW_EVENT_COLUMNS = {
    "location_type",
    "location_confidence",
    "coordinate_source",
    "incident_time",
    "detection_time",
    "source_time",
}


def test_legacy_event_store_schema_is_migrated(tmp_path):
    db_path = tmp_path / "events.db"

    with sqlite3.connect(db_path) as connection:
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
        connection.commit()

    EventStore(db_path)

    with sqlite3.connect(db_path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(events)"
            ).fetchall()
        }

    assert NEW_EVENT_COLUMNS.issubset(columns)


def test_create_event_persists_data_quality_metadata(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Wildfire near Novorossiysk",
        confidence=0.9,
        latitude=44.724,
        longitude=37.7691,
        location_type="city",
        location_confidence=0.72,
        coordinate_source="canonical_database",
        incident_time="2026-09-14T10:00:00Z",
        detection_time="2026-09-14T10:30:00Z",
        source_time="2026-09-14T11:00:00Z",
    )

    event = store.get_event_record(
        event_id
    )

    assert event["location"] == {
        "name": "Novorossiysk",
        "latitude": 44.724,
        "longitude": 37.7691,
        "type": "city",
        "confidence": 0.72,
        "source": "canonical_database",
    }

    assert event["time"] == {
        "incident_time": "2026-09-14T10:00:00+00:00",
        "detection_time": "2026-09-14T10:30:00+00:00",
        "source_time": "2026-09-14T11:00:00+00:00",
    }


def test_metadata_setters_preserve_existing_values_by_default(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Novorossiysk",
        primary_title="Industrial fire",
        location_type="city",
        location_confidence=0.6,
        coordinate_source="canonical_database",
        incident_time="2026-09-14T08:00:00Z",
    )

    changed_location = store.set_event_location_metadata(
        event_id=event_id,
        location_type="facility",
        location_confidence=0.95,
        coordinate_source="llm_extraction",
    )

    changed_time = store.set_event_time_metadata(
        event_id=event_id,
        incident_time="2026-09-14T09:00:00Z",
    )

    assert changed_location is False
    assert changed_time is False

    event = store.get_event_record(
        event_id
    )

    assert event["location"]["type"] == "city"
    assert event["location"]["confidence"] == 0.6
    assert (
        event["location"]["source"]
        == "canonical_database"
    )
    assert (
        event["time"]["incident_time"]
        == "2026-09-14T08:00:00+00:00"
    )


def test_metadata_setters_can_explicitly_overwrite(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Novorossiysk",
        primary_title="Industrial fire",
        location_type="city",
        location_confidence=0.6,
        coordinate_source="canonical_database",
        incident_time="2026-09-14T08:00:00Z",
    )

    assert store.set_event_location_metadata(
        event_id=event_id,
        location_type="facility",
        location_confidence=0.95,
        coordinate_source="llm_extraction",
        overwrite=True,
    )

    assert store.set_event_time_metadata(
        event_id=event_id,
        incident_time="2026-09-14T09:00:00Z",
        source_time="2026-09-14T09:15:00Z",
        overwrite=True,
    )

    event = store.get_event_record(
        event_id
    )

    assert event["location"]["type"] == "facility"
    assert event["location"]["confidence"] == 0.95
    assert event["location"]["source"] == "llm_extraction"

    assert (
        event["time"]["incident_time"]
        == "2026-09-14T09:00:00+00:00"
    )
    assert (
        event["time"]["source_time"]
        == "2026-09-14T09:15:00+00:00"
    )


def test_location_confidence_must_be_between_zero_and_one(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    with pytest.raises(ValueError):
        store.create_event(
            category="wildfire",
            location_name="Novorossiysk",
            primary_title="Wildfire",
            location_confidence=1.4,
        )
