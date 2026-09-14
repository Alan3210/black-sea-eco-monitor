from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)
from agents.news_agent.legal_followup_guard import (
    apply_legal_followup_guard,
    has_legal_follow_up_signal,
)
from agents.news_agent.models import NewsItem


def make_item(title, summary=None):
    return NewsItem(
        title=title,
        url="https://example.com/story",
        source="Test Source",
        published_at="2026-09-14T12:00:00+03:00",
        summary=summary,
    )


def make_result():
    return NewsClassification(
        classification="incident",
        category="oil_spill",
        location_name="Kerch Strait",
        location_type="water_body",
        location_confidence=0.9,
        is_black_sea_region=True,
        confidence=0.8,
        is_new_event=True,
        event_date=None,
        incident_time=None,
        reason="An oil spill is mentioned.",
    )


def test_kerch_lawsuit_headline_is_legal_follow_up():
    item = make_item(
        "Разлив нефти в Керченском проливе: "
        "суд принял уточненный иск к судовладельцам"
    )

    result = apply_legal_followup_guard(
        item,
        make_result(),
    )

    assert (
        result.classification
        == NewsClassificationType.follow_up
    )
    assert result.is_new_event is False
    assert (
        result.category.value
        == "oil_spill"
    )


def test_compensation_claim_is_legal_follow_up():
    item = make_item(
        "После разлива топлива компания потребовала "
        "возмещение ущерба через суд"
    )

    assert has_legal_follow_up_signal(
        item
    )

    result = apply_legal_followup_guard(
        item,
        make_result(),
    )

    assert (
        result.classification
        == NewsClassificationType.follow_up
    )


def test_real_incident_without_legal_signal_is_unchanged():
    item = make_item(
        "Нефть разлилась в Керченском проливе, "
        "идут работы по локализации"
    )

    original = make_result()

    result = apply_legal_followup_guard(
        item,
        original,
    )

    assert result == original


def test_noise_is_not_promoted_to_follow_up():
    item = make_item(
        "Суд рассмотрит спор двух компаний"
    )

    original = NewsClassification(
        classification="noise",
        category=None,
        location_name=None,
        is_black_sea_region=None,
        confidence=0.8,
        reason="No environmental incident.",
    )

    result = apply_legal_followup_guard(
        item,
        original,
    )

    assert result == original
