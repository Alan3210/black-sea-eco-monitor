import feedparser

from agents.news_agent.models import NewsItem


def collect_rss(
    feed_url: str,
    source_name: str
) -> list[NewsItem]:

    if not feed_url:
        raise ValueError(
            "NEWS_RSS_URL is not configured"
        )

    feed = feedparser.parse(
        feed_url
    )

    entries = getattr(
        feed,
        "entries",
        []
    )

    if getattr(feed, "bozo", False) and not entries:

        error = getattr(
            feed,
            "bozo_exception",
            "Unknown RSS parsing error"
        )

        raise RuntimeError(
            f"Failed to read RSS feed: {error}"
        )


    items = []


    for entry in entries:

        title = (
            entry.get("title")
            or ""
        ).strip()

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

        item_source = (
            entry_source.get("title")
            if entry_source
            else None
        ) or source_name


        item = NewsItem(

            title=title,

            url=url,

            source=item_source,

            published_at=entry.get(
                "published"
            ),

            summary=entry.get(
                "summary"
            )
        )


        items.append(item)


    return items