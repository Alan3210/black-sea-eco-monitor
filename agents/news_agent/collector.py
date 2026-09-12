import html
import logging
import re

import feedparser

from agents.news_agent.models import NewsItem
from agents.news_agent.sources import (
    NEWS_SOURCES,
    NewsSource,
)


logger = logging.getLogger(__name__)


MAX_ITEMS_PER_SOURCE = 40


def clean_text(
    value: str | None
) -> str | None:

    if not value:
        return None

    value = html.unescape(
        value
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    value = value.strip()

    return value or None


def normalize_title(
    title: str
) -> str:

    title = title.lower()

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def collect_source(
    source: NewsSource
) -> list[NewsItem]:

    feed = feedparser.parse(
        source.url
    )

    entries = getattr(
        feed,
        "entries",
        []
    )

    if (
        getattr(feed, "bozo", False)
        and not entries
    ):

        error = getattr(
            feed,
            "bozo_exception",
            "Unknown feed parsing error"
        )

        raise RuntimeError(
            f"{source.name}: {error}"
        )

    items = []

    for entry in entries[
        :MAX_ITEMS_PER_SOURCE
    ]:

        title = clean_text(
            entry.get("title")
        )

        url = (
            entry.get("link")
            or ""
        ).strip()

        if not title or not url:
            continue

        entry_source = entry.get(
            "source",
            {}
        )

        if entry_source:

            publisher = (
                entry_source.get("title")
                or source.name
            )

        else:

            publisher = source.name

        published_at = (
            entry.get("published")
            or entry.get("updated")
        )

        summary = clean_text(
            entry.get("summary")
            or entry.get("description")
        )

        items.append(
            NewsItem(
                title=title,
                url=url,
                source=publisher,
                published_at=published_at,
                summary=summary,
            )
        )

    return items


def deduplicate_items(
    items: list[NewsItem]
) -> list[NewsItem]:

    unique_items = []

    seen_titles = set()

    for item in items:

        key = normalize_title(
            item.title
        )

        if key in seen_titles:
            continue

        seen_titles.add(
            key
        )

        unique_items.append(
            item
        )

    return unique_items


def collect_all_sources(
    sources: list[NewsSource] | None = None
) -> list[NewsItem]:

    if sources is None:

        sources = NEWS_SOURCES

    collected_items = []

    for source in sources:

        if not source.enabled:
            continue

        try:

            source_items = collect_source(
                source
            )

            collected_items.extend(
                source_items
            )

            print(
                f"[SOURCE] {source.name}: "
                f"{len(source_items)} items"
            )

        except Exception as error:

            logger.warning(
                "Failed to collect source '%s': %s",
                source.name,
                error,
            )

            print(
                f"[SOURCE ERROR] "
                f"{source.name}: "
                f"{error}"
            )

    unique_items = deduplicate_items(
        collected_items
    )

    print()
    print(
        f"[COLLECTOR] Raw items: "
        f"{len(collected_items)}"
    )

    print(
        f"[COLLECTOR] Unique items: "
        f"{len(unique_items)}"
    )

    return unique_items