from agents.news_agent.category_evidence_guard import (
    apply_category_evidence_guard,
)
from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)
from agents.news_agent.models import NewsItem
from backend.models.event import EventCategory


def make_item(
    title: str
) -> NewsItem:

    return NewsItem(
        title=title,
        url="https://example.com",
        source="Test Source",
        published_at=(
            "Thu, 10 Sep 2026 07:00:00 GMT"
        ),
        summary=None,
    )


def make_industrial_fire_result() -> NewsClassification:

    return NewsClassification(
        classification=
        NewsClassificationType.incident,
        category=EventCategory.industrial_fire,
        location_name="Sevastopol",
        confidence=0.85,
        is_new_event=True,
        event_date=None,
        reason="Industrial fire detected.",
    )


def test_generic_urban_fire_loses_industrial_category():

    item = make_item(
        "Севастопольские огнеборцы ликвидируют "
        "пожар в районе улицы Горпищенко"
    )

    result = apply_category_evidence_guard(
        item,
        make_industrial_fire_result(),
    )

    assert result.category is None
    assert result.confidence <= 0.69


def test_terminal_fire_keeps_industrial_category():

    item = make_item(
        "Новороссийск атаковали беспилотники, "
        "сообщается о пожаре на мазутном терминале"
    )

    result = apply_category_evidence_guard(
        item,
        make_industrial_fire_result(),
    )

    assert (
        result.category
        == EventCategory.industrial_fire
    )
