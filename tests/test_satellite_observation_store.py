import sqlite3

from agents.news_agent.event_store import EventStore


SATELLITE_OBSERVATION_COLUMNS = {
    "id",
    "information_type",
    "derivation_level",
    "observation_type",
    "sensor",
    "platform",
    "dataset_id",
    "source_image_id",
    "acquisition_time",
    "processing_time",
    "geometry_geojson",
    "bbox_min_lon",
    "bbox_min_lat",
    "bbox_max_lon",
    "bbox_max_lat",
    "confidence",
    "review_status",
    "processing_version",
    "processing_method",
    "cache_reference",
    "provenance_json",
    "created_at",
    "updated_at",
}

EVENT_SATELLITE_OBSERVATION_COLUMNS = {
    "event_id",
    "satellite_observation_id",
    "relation_type",
    "relation_confidence",
    "created_at",
}

EXPECTED_INDEXES = {
    "idx_satellite_observations_acquisition_time",
    "idx_satellite_observations_type",
    "idx_satellite_observations_dataset",
    "idx_satellite_observations_source_image",
    "idx_satellite_observations_review_status",
    "idx_event_satellite_event",
}


def _table_columns(connection, table_name):
    return {
        row[1]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    }


def test_event_store_creates_satellite_tables(tmp_path):
    db_path = tmp_path / "events.db"

    EventStore(db_path)

    with sqlite3.connect(db_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        satellite_columns = _table_columns(
            connection,
            "satellite_observations",
        )
        link_columns = _table_columns(
            connection,
            "event_satellite_observations",
        )

    assert {
        "events",
        "event_evidence",
        "event_status_history",
        "satellite_observations",
        "event_satellite_observations",
    }.issubset(table_names)

    assert SATELLITE_OBSERVATION_COLUMNS == satellite_columns
    assert EVENT_SATELLITE_OBSERVATION_COLUMNS == link_columns


def test_event_store_creates_satellite_indexes(tmp_path):
    db_path = tmp_path / "events.db"

    EventStore(db_path)

    with sqlite3.connect(db_path) as connection:
        index_names = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                """
            ).fetchall()
        }

    assert EXPECTED_INDEXES.issubset(index_names)


def test_event_satellite_link_has_composite_primary_key_and_declared_foreign_keys(
    tmp_path,
):
    db_path = tmp_path / "events.db"

    EventStore(db_path)

    with sqlite3.connect(db_path) as connection:
        table_info = connection.execute(
            """
            PRAGMA table_info(event_satellite_observations)
            """
        ).fetchall()

        primary_key_positions = {
            row[1]: row[5]
            for row in table_info
            if row[5] > 0
        }

        foreign_keys = connection.execute(
            """
            PRAGMA foreign_key_list(event_satellite_observations)
            """
        ).fetchall()

        foreign_key_targets = {
            (row[3], row[2], row[4])
            for row in foreign_keys
        }

    assert primary_key_positions == {
        "event_id": 1,
        "satellite_observation_id": 2,
    }

    assert (
        "event_id",
        "events",
        "id",
    ) in foreign_key_targets

    assert (
        "satellite_observation_id",
        "satellite_observations",
        "id",
    ) in foreign_key_targets
