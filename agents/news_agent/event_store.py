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

            cursor.execute(
                "PRAGMA table_info(events)"
            )

            event_columns = {
                row[1]
                for row in cursor.fetchall()
            }

            if "latitude" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN latitude REAL
                    """
                )

            if "longitude" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN longitude REAL
                    """
                )

            if "location_type" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN location_type TEXT
                    """
                )

            if "location_confidence" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN location_confidence REAL
                    """
                )

            if "coordinate_source" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN coordinate_source TEXT
                    """
                )

            if "incident_time" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN incident_time TEXT
                    """
                )

            if "detection_time" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN detection_time TEXT
                    """
                )

            if "source_time" not in event_columns:
                cursor.execute(
                    """
                    ALTER TABLE events
                    ADD COLUMN source_time TEXT
                    """
                )

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
                CREATE TABLE IF NOT EXISTS satellite_observations (
                    id TEXT PRIMARY KEY,

                    information_type TEXT NOT NULL,
                    derivation_level TEXT NOT NULL,
                    observation_type TEXT NOT NULL,

                    sensor TEXT NOT NULL,
                    platform TEXT,
                    dataset_id TEXT NOT NULL,
                    source_image_id TEXT NOT NULL,

                    acquisition_time TEXT NOT NULL,
                    processing_time TEXT,

                    geometry_geojson TEXT,

                    bbox_min_lon REAL,
                    bbox_min_lat REAL,
                    bbox_max_lon REAL,
                    bbox_max_lat REAL,

                    confidence REAL,
                    review_status TEXT NOT NULL,

                    processing_version TEXT NOT NULL,
                    processing_method TEXT,

                    cache_reference TEXT,
                    provenance_json TEXT,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_satellite_observations (
                    event_id TEXT NOT NULL,
                    satellite_observation_id TEXT NOT NULL,

                    relation_type TEXT NOT NULL,
                    relation_confidence REAL,

                    created_at TEXT NOT NULL,

                    PRIMARY KEY (
                        event_id,
                        satellite_observation_id
                    ),

                    FOREIGN KEY(event_id)
                        REFERENCES events(id),

                    FOREIGN KEY(satellite_observation_id)
                        REFERENCES satellite_observations(id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_satellite_observations_acquisition_time
                ON satellite_observations(acquisition_time)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_satellite_observations_type
                ON satellite_observations(observation_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_satellite_observations_dataset
                ON satellite_observations(dataset_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_satellite_observations_source_image
                ON satellite_observations(source_image_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_satellite_observations_review_status
                ON satellite_observations(review_status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_event_satellite_event
                ON event_satellite_observations(event_id)
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

    @staticmethod
    def _normalize_confidence(value):
        if value is None:
            return None

        confidence = float(value)

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        return confidence

    @staticmethod
    def _normalize_optional_datetime(value):
        if value is None:
            return None

        parsed = parse_news_datetime(value)

        if parsed is None:
            raise ValueError(
                f"Invalid datetime value: {value!r}"
            )

        return parsed.isoformat()

    def create_event(
        self,
        *,
        category: str,
        location_name: str,
        primary_title: str,
        status: str = "detected",
        severity: str = "medium",
        confidence: float = 0.0,
        latitude: float | None = None,
        longitude: float | None = None,
        location_type: str | None = None,
        location_confidence: float | None = None,
        coordinate_source: str | None = None,
        incident_time=None,
        detection_time=None,
        source_time=None,
    ):
        now = datetime.now(timezone.utc).isoformat()
        event_id = "evt_" + str(uuid4())

        location_confidence = (
            self._normalize_confidence(
                location_confidence
            )
        )

        incident_time = self._normalize_optional_datetime(
            incident_time
        )
        detection_time = self._normalize_optional_datetime(
            detection_time
        ) or now
        source_time = self._normalize_optional_datetime(
            source_time
        )

        with self._connect() as connection:
            connection.execute("""
                INSERT INTO events (
                    id, category, location_name, primary_title,
                    status, severity, confidence,
                    first_seen, last_seen,
                    created_at, updated_at,
                    latitude, longitude,
                    location_type, location_confidence,
                    coordinate_source,
                    incident_time, detection_time, source_time
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
            """, (
                event_id, category, location_name, primary_title,
                status, severity, confidence,
                now, now, now, now,
                latitude, longitude,
                location_type, location_confidence,
                coordinate_source,
                incident_time, detection_time, source_time
            ))
            connection.commit()

        return event_id

    def list_event_records(self):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    e.id,
                    e.category,
                    e.location_name,
                    e.primary_title,
                    e.status,
                    e.severity,
                    e.confidence,
                    e.first_seen,
                    e.last_seen,
                    e.created_at,
                    e.updated_at,
                    e.latitude,
                    e.longitude,
                    e.location_type,
                    e.location_confidence,
                    e.coordinate_source,
                    e.incident_time,
                    e.detection_time,
                    e.source_time,
                    (
                        SELECT COUNT(*)
                        FROM event_evidence AS ev
                        WHERE ev.event_id = e.id
                    ) AS evidence_count
                FROM events AS e
                ORDER BY
                    e.updated_at DESC,
                    e.created_at DESC
                """
            )

            rows = cursor.fetchall()

        return [
            self._event_row_to_record(
                row
            )
            for row in rows
        ]

    def get_event_record(
        self,
        event_id,
    ):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    e.id,
                    e.category,
                    e.location_name,
                    e.primary_title,
                    e.status,
                    e.severity,
                    e.confidence,
                    e.first_seen,
                    e.last_seen,
                    e.created_at,
                    e.updated_at,
                    e.latitude,
                    e.longitude,
                    e.location_type,
                    e.location_confidence,
                    e.coordinate_source,
                    e.incident_time,
                    e.detection_time,
                    e.source_time,
                    (
                        SELECT COUNT(*)
                        FROM event_evidence AS ev
                        WHERE ev.event_id = e.id
                    ) AS evidence_count
                FROM events AS e
                WHERE e.id = ?
                LIMIT 1
                """,
                (event_id,),
            )

            row = cursor.fetchone()

        if not row:
            return None

        return self._event_row_to_record(
            row
        )

    @staticmethod
    def _event_row_to_record(row):
        return {
            "id": row[0],
            "category": row[1],
            "location": {
                "name": row[2],
                "latitude": row[11],
                "longitude": row[12],
                "type": row[13],
                "confidence": row[14],
                "source": row[15],
            },
            "time": {
                "incident_time": row[16],
                "detection_time": row[17],
                "source_time": row[18],
            },
            "primary_title": row[3],
            "status": row[4],
            "severity": row[5],
            "confidence": row[6],
            "first_seen": row[7],
            "last_seen": row[8],
            "created_at": row[9],
            "updated_at": row[10],
            "evidence_count": row[19],
        }

    def get_event_evidence_records(
        self,
        event_id,
    ):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    event_id,
                    source,
                    title,
                    url,
                    published_at,
                    confidence,
                    reason,
                    created_at
                FROM event_evidence
                WHERE event_id = ?
                ORDER BY created_at ASC
                """,
                (event_id,),
            )

            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "event_id": row[1],
                "source": row[2],
                "title": row[3],
                "url": row[4],
                "published_at": row[5],
                "confidence": row[6],
                "reason": row[7],
                "created_at": row[8],
            }
            for row in rows
        ]

    def get_event_coordinates(
        self,
        event_id,
    ):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT latitude, longitude
                FROM events
                WHERE id = ?
                """,
                (event_id,),
            )

            row = cursor.fetchone()

        if not row:
            return None

        return row[0], row[1]

    def set_event_coordinates(
        self,
        *,
        event_id,
        latitude,
        longitude,
        overwrite=False,
    ):
        if (
            latitude is None
            or longitude is None
        ):
            return False

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as connection:
            cursor = connection.cursor()

            if overwrite:
                cursor.execute(
                    """
                    UPDATE events
                    SET latitude = ?,
                        longitude = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        latitude,
                        longitude,
                        now,
                        event_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE events
                    SET latitude = ?,
                        longitude = ?,
                        updated_at = ?
                    WHERE id = ?
                      AND (
                          latitude IS NULL
                          OR longitude IS NULL
                      )
                    """,
                    (
                        latitude,
                        longitude,
                        now,
                        event_id,
                    ),
                )

            changed = cursor.rowcount > 0
            connection.commit()

        return changed

    def set_event_location_metadata(
        self,
        *,
        event_id,
        location_type=None,
        location_confidence=None,
        coordinate_source=None,
        overwrite=False,
    ):
        values = {
            "location_type": location_type,
            "location_confidence": (
                self._normalize_confidence(
                    location_confidence
                )
                if location_confidence is not None
                else None
            ),
            "coordinate_source": coordinate_source,
        }

        return self._update_optional_event_fields(
            event_id=event_id,
            values=values,
            overwrite=overwrite,
        )

    def set_event_time_metadata(
        self,
        *,
        event_id,
        incident_time=None,
        detection_time=None,
        source_time=None,
        overwrite=False,
    ):
        values = {
            "incident_time": (
                self._normalize_optional_datetime(
                    incident_time
                )
                if incident_time is not None
                else None
            ),
            "detection_time": (
                self._normalize_optional_datetime(
                    detection_time
                )
                if detection_time is not None
                else None
            ),
            "source_time": (
                self._normalize_optional_datetime(
                    source_time
                )
                if source_time is not None
                else None
            ),
        }

        return self._update_optional_event_fields(
            event_id=event_id,
            values=values,
            overwrite=overwrite,
        )

    def _update_optional_event_fields(
        self,
        *,
        event_id,
        values,
        overwrite,
    ):
        provided = {
            column: value
            for column, value in values.items()
            if value is not None
        }

        if not provided:
            return False

        now = datetime.now(
            timezone.utc
        ).isoformat()

        columns = list(provided)

        if overwrite:
            assignments = [
                f"{column} = ?"
                for column in columns
            ]
            where_extra = ""
        else:
            assignments = [
                f"{column} = COALESCE({column}, ?)"
                for column in columns
            ]
            null_checks = " OR ".join(
                f"{column} IS NULL"
                for column in columns
            )
            where_extra = (
                f" AND ({null_checks})"
            )

        assignments.append(
            "updated_at = ?"
        )

        parameters = [
            provided[column]
            for column in columns
        ]
        parameters.extend([
            now,
            event_id,
        ])

        sql = (
            "UPDATE events SET "
            + ", ".join(assignments)
            + " WHERE id = ?"
            + where_extra
        )

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                sql,
                parameters,
            )
            changed = cursor.rowcount > 0
            connection.commit()

        return changed

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
