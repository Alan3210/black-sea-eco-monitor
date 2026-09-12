from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
import re

from agents.news_agent.classification import NewsClassification
from agents.news_agent.models import NewsItem


CORRELATION_MAX_HOURS = 72
MIN_TITLE_SIMILARITY = 0.45


@dataclass
class EventCandidate:
    item: NewsItem
    classification: NewsClassification


@dataclass
class CorrelationDecision:
    is_same_event: bool
    similarity: float
    reason: str


def normalize_location(
    value: str | None,
) -> str | None:

    if not value:
        return None

    normalized = value.lower()

    normalized = re.sub(
        r"[^a-zа-яё0-9]+",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip() or None


def normalize_title(
    title: str,
) -> str:

    # Google News titles often end with:
    # "... - Publisher Name"
    #
    # Remove that suffix so publisher names do not affect
    # article-to-article similarity.
    if " - " in title:
        title = title.rsplit(
            " - ",
            1,
        )[0]

    title = title.lower()

    title = re.sub(
        r"[^a-zа-яё0-9]+",
        " ",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip()


def calculate_title_similarity(
    first_title: str,
    second_title: str,
) -> float:

    first = normalize_title(
        first_title
    )

    second = normalize_title(
        second_title
    )

    if not first or not second:
        return 0.0

    return SequenceMatcher(
        None,
        first,
        second,
    ).ratio()


def parse_published_at(
    value: str | None,
) -> datetime | None:

    if not value:
        return None

    try:

        parsed = parsedate_to_datetime(
            value
        )

    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:

        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def calculate_time_distance_hours(
    first: NewsItem,
    second: NewsItem,
) -> float | None:

    first_time = parse_published_at(
        first.published_at
    )

    second_time = parse_published_at(
        second.published_at
    )

    if (
        first_time is None
        or second_time is None
    ):
        return None

    difference = abs(
        first_time - second_time
    )

    return (
        difference.total_seconds()
        / 3600
    )


def evaluate_event_correlation(
    first: EventCandidate,
    second: EventCandidate,
) -> CorrelationDecision:

    first_category = (
        first.classification.category
    )

    second_category = (
        second.classification.category
    )

    # --------------------------------------------------
    # 1. Both candidates must have a category.
    # --------------------------------------------------

    if (
        first_category is None
        or second_category is None
    ):

        return CorrelationDecision(
            is_same_event=False,
            similarity=0.0,
            reason=(
                "At least one candidate has no "
                "environmental category."
            ),
        )

    # --------------------------------------------------
    # 2. Categories must match.
    # --------------------------------------------------

    if first_category != second_category:

        return CorrelationDecision(
            is_same_event=False,
            similarity=0.0,
            reason=(
                "The environmental categories differ."
            ),
        )

    # --------------------------------------------------
    # 3. Locations must be known and must match.
    # --------------------------------------------------

    first_location = normalize_location(
        first.classification.location_name
    )

    second_location = normalize_location(
        second.classification.location_name
    )

    if (
        first_location is None
        or second_location is None
    ):

        return CorrelationDecision(
            is_same_event=False,
            similarity=0.0,
            reason=(
                "At least one candidate has no "
                "resolved location."
            ),
        )

    if first_location != second_location:

        return CorrelationDecision(
            is_same_event=False,
            similarity=0.0,
            reason=(
                "The resolved locations differ."
            ),
        )

    # --------------------------------------------------
    # 4. Reports must be close enough in publication time.
    #
    # We intentionally use publication time here instead
    # of LLM event_date. Event dates will later be handled
    # by a dedicated Event Date Resolver.
    # --------------------------------------------------

    distance_hours = (
        calculate_time_distance_hours(
            first.item,
            second.item,
        )
    )

    if (
        distance_hours is not None
        and distance_hours
        > CORRELATION_MAX_HOURS
    ):

        return CorrelationDecision(
            is_same_event=False,
            similarity=0.0,
            reason=(
                "The reports are too far apart in time."
            ),
        )

    # --------------------------------------------------
    # 5. Titles must still be meaningfully similar.
    #
    # This deliberately makes correlation conservative:
    # it is safer to keep two event clusters separate than
    # accidentally merge two different fires in the same
    # city on the same day.
    # --------------------------------------------------

    similarity = calculate_title_similarity(
        first.item.title,
        second.item.title,
    )

    if similarity < MIN_TITLE_SIMILARITY:

        return CorrelationDecision(
            is_same_event=False,
            similarity=similarity,
            reason=(
                "The titles are not similar enough "
                "for conservative correlation."
            ),
        )

    return CorrelationDecision(
        is_same_event=True,
        similarity=similarity,
        reason=(
            "Category, location, time window and "
            "title similarity support the same event."
        ),
    )


def cluster_event_candidates(
    candidates: list[EventCandidate],
) -> list[list[EventCandidate]]:

    clusters: list[
        list[EventCandidate]
    ] = []

    for candidate in candidates:

        matched_cluster = None

        for cluster in clusters:

            # A candidate joins a cluster if it correlates
            # with at least one existing member.
            for existing in cluster:

                decision = (
                    evaluate_event_correlation(
                        candidate,
                        existing,
                    )
                )

                if decision.is_same_event:

                    matched_cluster = cluster
                    break

            if matched_cluster is not None:
                break

        if matched_cluster is None:

            clusters.append(
                [candidate]
            )

        else:

            matched_cluster.append(
                candidate
            )

    return clusters
