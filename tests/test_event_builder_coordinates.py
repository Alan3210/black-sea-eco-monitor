from types import SimpleNamespace

from agents.news_agent.event_builder import (
    build_environmental_event,
    build_event_location,
)


def test_build_event_location_uses_known_coordinates():
    location = build_event_location(
        "Novorossiysk"
    )

    assert location.latitude == 44.7240
    assert location.longitude == 37.7691


def test_build_event_location_falls_back_for_unknown_location():
    location = build_event_location(
        "Unknown Place"
    )

    assert location.latitude == 0.0
    assert location.longitude == 0.0


def test_event_builder_uses_classification_location():
    item = SimpleNamespace(
        title="Test wildfire report",
        source="Test Source",
        url="https://example.com/report",
    )

    classification = SimpleNamespace(
        category="wildfire",
        confidence=0.8,
        location_name="Utrish Reserve",
        reason="Test event.",
    )

    event = build_environmental_event(
        item,
        classification,
    )

    assert event.location.latitude == 44.7605
    assert event.location.longitude == 37.3854
