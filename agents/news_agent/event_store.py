from multiprocessing.dummy import connection
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


DEFAULT_DB_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "database"
    / "events.db"
)


class EventStore:

    def __init__(
        self,
        db_path: str | Path | None = None,
    ):

        self.db_path = Path(
            db_path or DEFAULT_DB_PATH
        )

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._init_database()


    def _connect(self):
        return sqlite3.connect(
            self.db_path
        )


    def _init_database(self):

        with self._connect() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
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

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS event_evidence (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    source TEXT,
                    title TEXT,
                    url TEXT,
                    published_at TEXT,
                    confidence REAL,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id)
                        REFERENCES events(id)
                )
                """
            )

            connection.commit()


    def create_event(
        self,
        *,
        category: str,
        location_name: str,
        primary_title: str,
        status: str = "detected",
        severity: str = "medium",
        confidence: float = 0.0,
    ):

        now = datetime.now(
            timezone.utc
        ).isoformat()

        event_id = (
            "evt_"
            + str(uuid4())
        )

        with self._connect() as connection:

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    category,
                    location_name,
                    primary_title,
                    status,
                    severity,
                    confidence,
                    now,
                    now,
                    now,
                    now,
                ),
            )

            connection.commit()

        return event_id


    def get_candidate_events(
        self,
        *,
        category: str,
        location_name: str,
    ):

        with self._connect() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    category,
                    location_name,
                    primary_title,
                    created_at
                FROM events
                WHERE category = ?
                AND location_name = ?
                ORDER BY created_at DESC
                """,
                (
                    category,
                    location_name,
                ),
            )

            return cursor.fetchall()


    def find_matching_event(
        self,
        *,
        category: str,
        location_name: str,
        title: str | None = None,
    ):

        candidates = self.get_candidate_events(
            category=category,
            location_name=location_name,
        )

        if not candidates:
            return None

        if title is None:
            return candidates[0][0]

        from agents.news_agent.event_matcher import (
            calculate_event_match,
        )

        best_match = None
        best_score = 0.0

        for candidate in candidates:

            result = calculate_event_match(
                existing_title=candidate[3],
                new_title=title,
                existing_category=candidate[1],
                new_category=category,
                existing_location=candidate[2],
                new_location=location_name,
            )

            if (
                result.is_match
                and result.score > best_score
            ):
                best_match = candidate[0]
                best_score = result.score

        return best_match


    def add_evidence(
        self,
        *,
        event_id: str,
        source: str,
        title: str,
        url: str | None,
        published_at: str | None,
        confidence: float,
        reason: str,
    ):

        evidence_id = (
            "ev_"
            + str(uuid4())
        )

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as connection:

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
                    evidence_id,
                    event_id,
                    source,
                    title,
                    url,
                    published_at,
                    confidence,
                    reason,
                    now,
                ),
            )

            connection.execute(
                """
                UPDATE events
                SET last_seen = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    now,
                    now,
                    event_id,
                ),
            )

            connection.commit()

            return evidence_id
        
            connection.commit()

            return evidence_id


    def get_event_evidence(
        self,
        event_id: str,
    ):

        with self._connect() as connection:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    source,
                    title,
                    confidence
                FROM event_evidence
                WHERE event_id = ?
                """,
                (event_id,),
            )

            return cursor.fetchall()