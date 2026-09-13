import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from email.utils import parsedate_to_datetime


STATUS_ORDER = {
    "detected": 0,
    "active": 1,
    "contained": 2,
    "resolved": 3,
}


EVENT_MATCH_WINDOW_HOURS = 72


def parse_news_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()

        if not text:
            return None

        try:
            parsed = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )
        except ValueError:
            try:
                parsed = parsedate_to_datetime(
                    text
                )
            except (
                TypeError,
                ValueError,
                OverflowError,
            ):
                return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "events.db"
)


class EventStore:

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_database(self):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute("""
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
            """)

            cursor.execute("""
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
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_status_history (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    reason TEXT,
                    evidence_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_event_evidence_event_url
                ON event_evidence(event_id, url)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_event_evidence_event_source_title
                ON event_evidence(event_id, source, title)
            """)

            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                uq_event_evidence_event_url
                ON event_evidence(event_id, url)
                WHERE url IS NOT NULL
                  AND length(trim(url)) > 0
            """)

            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                uq_event_evidence_event_source_title_no_url
                ON event_evidence(
                    event_id,
                    source,
                    title
                )
                WHERE url IS NULL
                   OR length(trim(url)) = 0
            """)

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
        now = datetime.now(timezone.utc).isoformat()
        event_id = "evt_" + str(uuid4())

        with self._connect() as connection:
            connection.execute("""
                INSERT INTO events (
                    id, category, location_name, primary_title,
                    status, severity, confidence,
                    first_seen, last_seen,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, category, location_name, primary_title,
                status, severity, confidence,
                now, now, now, now
            ))
            connection.commit()

        return event_id

    def get_candidate_events(self, *, category, location_name):
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, category, location_name, primary_title, created_at
                FROM events
                WHERE category = ?
                AND location_name = ?
                ORDER BY created_at DESC
            """, (category, location_name))
            return cursor.fetchall()

    def get_event_titles(
        self,
        event_id,
    ):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT primary_title
                FROM events
                WHERE id = ?
                """,
                (event_id,),
            )

            event_row = cursor.fetchone()

            if not event_row:
                return []

            titles = []

            primary_title = event_row[0]

            if primary_title:
                titles.append(
                    primary_title
                )

            cursor.execute(
                """
                SELECT title
                FROM event_evidence
                WHERE event_id = ?
                  AND title IS NOT NULL
                  AND length(trim(title)) > 0
                ORDER BY created_at ASC
                """,
                (event_id,),
            )

            for row in cursor.fetchall():
                evidence_title = row[0]

                if (
                    evidence_title
                    and evidence_title not in titles
                ):
                    titles.append(
                        evidence_title
                    )

        return titles

    def get_event_latest_published_at(
        self,
        event_id,
    ):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT published_at
                FROM event_evidence
                WHERE event_id = ?
                  AND published_at IS NOT NULL
                """,
                (event_id,),
            )

            parsed_dates = []

            for row in cursor.fetchall():
                parsed = parse_news_datetime(
                    row[0]
                )

                if parsed is not None:
                    parsed_dates.append(
                        parsed
                    )

        if not parsed_dates:
            return None

        return max(
            parsed_dates
        )

    def _is_event_within_match_window(
        self,
        *,
        event_id,
        published_at,
    ):
        new_time = parse_news_datetime(
            published_at
        )

        if new_time is None:
            return True

        existing_time = (
            self.get_event_latest_published_at(
                event_id
            )
        )

        if existing_time is None:
            return True

        difference = abs(
            new_time - existing_time
        )

        return difference <= timedelta(
            hours=EVENT_MATCH_WINDOW_HOURS
        )

    def find_matching_event(
        self,
        *,
        category,
        location_name,
        title=None,
        published_at=None,
    ):
        candidates = self.get_candidate_events(
            category=category,
            location_name=location_name,
        )

        if not candidates:
            return None

        if title is None:
            for candidate in candidates:
                event_id = candidate[0]

                if self._is_event_within_match_window(
                    event_id=event_id,
                    published_at=published_at,
                ):
                    return event_id

            return None

        from agents.news_agent.event_matcher import calculate_event_match

        best = None
        best_score = 0.0

        for candidate in candidates:
            event_id = candidate[0]

            if not self._is_event_within_match_window(
                event_id=event_id,
                published_at=published_at,
            ):
                continue

            candidate_titles = (
                self.get_event_titles(
                    event_id
                )
            )

            if not candidate_titles:
                candidate_titles = [
                    candidate[3]
                ]

            candidate_best_score = 0.0

            for existing_title in candidate_titles:
                result = calculate_event_match(
                    existing_title=existing_title,
                    new_title=title,
                    existing_category=candidate[1],
                    new_category=category,
                    existing_location=candidate[2],
                    new_location=location_name,
                )

                if (
                    result.is_match
                    and result.score
                    > candidate_best_score
                ):
                    candidate_best_score = (
                        result.score
                    )

            if (
                candidate_best_score
                > best_score
            ):
                best = event_id
                best_score = (
                    candidate_best_score
                )

        return best

    def find_existing_evidence_id(
        self,
        *,
        event_id,
        source,
        title,
        url,
    ):
        normalized_url = (
            url.strip()
            if isinstance(url, str)
            else None
        )

        with self._connect() as connection:
            cursor = connection.cursor()

            if normalized_url:
                cursor.execute(
                    """
                    SELECT id
                    FROM event_evidence
                    WHERE event_id = ?
                    AND url = ?
                    LIMIT 1
                    """,
                    (
                        event_id,
                        normalized_url,
                    ),
                )
            else:
                cursor.execute(
                    """
                    SELECT id
                    FROM event_evidence
                    WHERE event_id = ?
                    AND source = ?
                    AND title = ?
                    LIMIT 1
                    """,
                    (
                        event_id,
                        source,
                        title,
                    ),
                )

            row = cursor.fetchone()

        return row[0] if row else None

    def find_event_by_evidence_url(
        self,
        url: str,
    ):
        if not url:
            return None

        normalized_url = url.strip()

        if not normalized_url:
            return None

        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT event_id
                FROM event_evidence
                WHERE url = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (normalized_url,),
            )

            row = cursor.fetchone()

        return row[0] if row else None

    def add_evidence(
        self,
        *,
        event_id,
        source,
        title,
        url,
        published_at,
        confidence,
        reason,
    ):
        normalized_url = (
            url.strip()
            if isinstance(url, str)
            else None
        )

        existing_evidence_id = (
            self.find_existing_evidence_id(
                event_id=event_id,
                source=source,
                title=title,
                url=normalized_url,
            )
        )

        if existing_evidence_id is not None:
            return existing_evidence_id

        evidence_id = "ev_" + str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.execute("""
                INSERT INTO event_evidence (
                    id, event_id, source, title, url,
                    published_at, confidence, reason, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence_id, event_id, source, title, normalized_url,
                published_at, confidence, reason, now
            ))

            connection.execute("""
                UPDATE events
                SET last_seen = ?, updated_at = ?
                WHERE id = ?
            """, (now, now, event_id))

            connection.commit()

        return evidence_id

    def get_event_evidence(self, event_id):
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT source, title, confidence
                FROM event_evidence
                WHERE event_id = ?
            """, (event_id,))
            return cursor.fetchall()

    def add_status_history(
        self,
        *,
        event_id,
        old_status,
        new_status,
        reason,
        evidence_id=None,
    ):
        history_id = "st_" + str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.execute("""
                INSERT INTO event_status_history (
                    id, event_id, old_status, new_status,
                    reason, evidence_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                history_id, event_id, old_status,
                new_status, reason, evidence_id, now
            ))
            connection.commit()

        return history_id

    def update_status(
        self,
        *,
        event_id,
        new_status,
        reason,
        evidence_id=None,
    ):
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT status FROM events WHERE id = ?",
                (event_id,),
            )

            row = cursor.fetchone()

            if not row:
                return None

            old_status = row[0]

            if old_status == new_status:
                return None

            old_rank = STATUS_ORDER.get(old_status)
            new_rank = STATUS_ORDER.get(new_status)

            if (
                old_rank is not None
                and new_rank is not None
                and new_rank < old_rank
            ):
                return None

            now = datetime.now(timezone.utc).isoformat()

            connection.execute("""
                UPDATE events
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (new_status, now, event_id))

            connection.commit()

        return self.add_status_history(
            event_id=event_id,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            evidence_id=evidence_id,
        )

    def get_status_history(self, event_id):
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT old_status, new_status, reason
                FROM event_status_history
                WHERE event_id = ?
                ORDER BY created_at
            """, (event_id,))
            return cursor.fetchall()
