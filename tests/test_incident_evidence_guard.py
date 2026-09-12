from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)
from agents.news_agent.incident_evidence_guard import (
    apply_incident_evidence_guard,
)
from backend.models.event import EventCategory


def make_result(
    *,
    category,
    confidence,
    is_new_event,
) -> NewsClassification:

    return NewsClassification(
        classification=
        NewsClassificationType.incident,
        category=category,
        location_name="Novorossiysk",
        is_black_sea_region=True,
        confidence=confidence,
        is_new_event=is_new_event,
        event_date=None,
        reason="Test incident.",
    )


def test_confirmed_incident_is_promoted_and_confidence_is_floored():

    llm_result = make_result(
        category=EventCategory.industrial_fire,
        confidence=0.6,
        is_new_event=None,
    )

    rule_result = make_result(
        category=EventCategory.industrial_fire,
        confidence=0.7,
        is_new_event=None,
    )

    result = apply_incident_evidence_guard(
        llm_result,
        rule_result,
    )

    assert result.is_new_event is True
    assert result.confidence == 0.8


def test_uncategorized_incident_is_not_promoted():

    llm_result = make_result(
        category=None,
        confidence=0.8,
        is_new_event=None,
    )

    rule_result = make_result(
        category=None,
        confidence=0.7,
        is_new_event=None,
    )

    result = apply_incident_evidence_guard(
        llm_result,
        rule_result,
    )

    assert result.is_new_event is None
    assert result.confidence == 0.8
