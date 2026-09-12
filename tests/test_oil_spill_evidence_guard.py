from agents.news_agent.oil_spill_evidence_guard import (
    apply_oil_spill_evidence_guard,
)
from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)
from backend.models.event import EventCategory


class MockItem:
    def __init__(self, title, summary=""):
        self.title = title
        self.summary = summary


def make_oil_result():
    return NewsClassification(
        classification=NewsClassificationType.incident,
        category=EventCategory.oil_spill,
        location_name="Anapa",
        is_black_sea_region=True,
        confidence=0.8,
        is_new_event=True,
        event_date=None,
        reason="Test.",
    )


def test_legal_article_does_not_create_oil_spill():

    item = MockItem(
        "Владелец Волгонефти не хочет платить компенсацию за мазут"
    )

    result = apply_oil_spill_evidence_guard(
        item,
        make_oil_result(),
    )

    assert result.category is None


def test_real_spill_keeps_oil_spill():

    item = MockItem(
        "Произошел разлив мазута в Черное море"
    )

    result = apply_oil_spill_evidence_guard(
        item,
        make_oil_result(),
    )

    assert result.category == EventCategory.oil_spill
