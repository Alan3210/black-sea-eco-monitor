from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)

from agents.news_agent.event_gate import (
    EventGateAction,
    evaluate_event_candidate,
)

from backend.models.event import EventCategory


def test_black_sea_incident_creates_event():

    classification = NewsClassification(
        classification=NewsClassificationType.incident,
        category=EventCategory.water_pollution,
        location_name="Odesa",
        is_black_sea_region=True,
        confidence=0.95,
        is_new_event=True,
        event_date=None,
        reason="Confirmed sunflower oil spill.",
    )

    decision = evaluate_event_candidate(
        classification
    )

    assert decision.action == EventGateAction.create_event


def test_non_black_sea_incident_is_ignored():

    classification = NewsClassification(
        classification=NewsClassificationType.incident,
        category=EventCategory.water_pollution,
        location_name="Israel",
        is_black_sea_region=False,
        confidence=0.95,
        is_new_event=True,
        event_date=None,
        reason="Pollution incident in Israel.",
    )

    decision = evaluate_event_candidate(
        classification
    )

    assert decision.action == EventGateAction.ignore


def test_follow_up_is_attached():

    classification = NewsClassification(
        classification=NewsClassificationType.follow_up,
        category=EventCategory.oil_spill,
        location_name="Black Sea",
        is_black_sea_region=True,
        confidence=0.90,
        is_new_event=False,
        event_date=None,
        reason="Cleanup after an earlier oil spill.",
    )

    decision = evaluate_event_candidate(
        classification
    )

    assert (
        decision.action
        == EventGateAction.attach_follow_up
    )


def test_clear_report_is_ignored():

    classification = NewsClassification(
        classification=NewsClassificationType.clear,
        category=EventCategory.water_pollution,
        location_name="Bulgaria",
        is_black_sea_region=True,
        confidence=0.95,
        is_new_event=False,
        event_date=None,
        reason="No active pollution detected.",
    )

    decision = evaluate_event_candidate(
        classification
    )

    assert decision.action == EventGateAction.ignore