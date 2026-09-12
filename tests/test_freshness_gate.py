from datetime import datetime, timezone

from agents.news_agent.freshness_gate import (
    evaluate_news_freshness,
)

from agents.news_agent.models import NewsItem


TEST_NOW = datetime(
    2026,
    9,
    12,
    tzinfo=timezone.utc,
)


def make_news(
    published_at
):

    return NewsItem(
        title="Test environmental news",
        url="https://example.com",
        source="Test Source",
        published_at=published_at,
        summary=None,
    )


def test_recent_news_is_fresh():

    item = make_news(
        "Thu, 10 Sep 2026 07:00:00 GMT"
    )

    result = evaluate_news_freshness(
        item,
        now=TEST_NOW,
    )

    assert result.is_fresh is True


def test_old_news_is_not_fresh():

    item = make_news(
        "Sat, 01 Aug 2026 07:00:00 GMT"
    )

    result = evaluate_news_freshness(
        item,
        now=TEST_NOW,
    )

    assert result.is_fresh is False


def test_missing_date_is_not_fresh():

    item = make_news(
        None
    )

    result = evaluate_news_freshness(
        item,
        now=TEST_NOW,
    )

    assert result.is_fresh is False


def test_future_date_is_not_fresh():

    item = make_news(
        "Sun, 20 Sep 2026 07:00:00 GMT"
    )

    result = evaluate_news_freshness(
        item,
        now=TEST_NOW,
    )

    assert result.is_fresh is False