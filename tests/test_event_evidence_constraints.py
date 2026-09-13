import sqlite3

import pytest

from agents.news_agent.event_store import EventStore


def _create_event(store):
    return store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Forest fire",
        confidence=0.8,
    )


def test_database_rejects_duplicate_url_in_same_event(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = _create_event(store)

    store.add_evidence(
        event_id=event_id,
        source="Source A",
        title="Fire report",
        url="https://example.com/report",
        published_at=None,
        confidence=0.8,
        reason="Initial report",
    )

    with pytest.raises(
        sqlite3.IntegrityError
    ):
        with store._connect() as connection:
            connection.execute(
                """
                INSERT INTO event_evidence (
                    id,
                    event_id,
                    source,
                    title,
                    url,
                    published_at,
                    confidence,
                    reason,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ev_manual_duplicate",
                    event_id,
                    "Source B",
                    "Another title",
                    "https://example.com/report",
                    None,
                    0.8,
                    "Manual duplicate",
                    "2026-09-13T09:00:00+00:00",
                ),
            )


def test_database_rejects_duplicate_without_url(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = _create_event(store)

    store.add_evidence(
        event_id=event_id,
        source="Local Source",
        title="Fire contained",
        url=None,
        published_at=None,
        confidence=0.9,
        reason="Follow-up",
    )

    with pytest.raises(
        sqlite3.IntegrityError
    ):
        with store._connect() as connection:
            connection.execute(
                """
                INSERT INTO event_evidence (
                    id,
                    event_id,
                    source,
                    title,
                    url,
                    published_at,
                    confidence,
                    reason,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ev_manual_duplicate_no_url",
                    event_id,
                    "Local Source",
                    "Fire contained",
                    None,
                    None,
                    0.9,
                    "Manual duplicate",
                    "2026-09-13T09:00:00+00:00",
                ),
            )
