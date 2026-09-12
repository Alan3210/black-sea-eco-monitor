from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
import re


MATCH_WINDOW_HOURS = 72
MIN_SIMILARITY = 0.45


@dataclass
class EventMatchResult:
    is_match: bool
    score: float
    reason: str


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()

    value = re.sub(
        r"[^a-zа-яё0-9\s]+",
        " ",
        value,
    )

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def title_similarity(
    first: str | None,
    second: str | None,
) -> float:

    first_normalized = normalize_text(first)
    second_normalized = normalize_text(second)

    if not first_normalized or not second_normalized:
        return 0.0

    return SequenceMatcher(
        None,
        first_normalized,
        second_normalized,
    ).ratio()


def within_time_window(
    first_time: datetime | None,
    second_time: datetime | None,
) -> bool:

    if not first_time or not second_time:
        return True

    delta = abs(
        first_time - second_time
    )

    return (
        delta.total_seconds()
        <= MATCH_WINDOW_HOURS * 3600
    )


def calculate_event_match(
    *,
    existing_title: str,
    new_title: str,
    existing_category: str,
    new_category: str,
    existing_location: str,
    new_location: str,
    existing_time: datetime | None = None,
    new_time: datetime | None = None,
) -> EventMatchResult:

    if existing_category != new_category:

        return EventMatchResult(
            False,
            0.0,
            "Different categories.",
        )

    if (
        normalize_text(existing_location)
        != normalize_text(new_location)
    ):

        return EventMatchResult(
            False,
            0.0,
            "Different locations.",
        )

    if not within_time_window(
        existing_time,
        new_time,
    ):

        return EventMatchResult(
            False,
            0.0,
            "Events are outside time window.",
        )

    similarity = title_similarity(
        existing_title,
        new_title,
    )

    if similarity < MIN_SIMILARITY:

        return EventMatchResult(
            False,
            similarity,
            "Titles are not similar enough.",
        )

    return EventMatchResult(
        True,
        similarity,
        "Category, location, time and title similarity match.",
    )
