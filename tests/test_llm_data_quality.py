import pytest
from pydantic import ValidationError

from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
    NewsLocationType,
)
from agents.news_agent.llm_classifier import (
    _build_prompt,
)
from agents.news_agent.models import NewsItem


def make_item():
    return NewsItem(
        title="Wildfire reported near Novorossiysk",
        url="https://example.com/story",
        source="Test Source",
        published_at="2026-09-14T12:00:00+03:00",
        summary="The fire began at 08:30 in a named reserve.",
    )


def test_news_classification_accepts_location_quality_fields():
    result = NewsClassification(
        classification=NewsClassificationType.incident,
        category="wildfire",
        location_name="Utrish Reserve",
        location_type=NewsLocationType.protected_area,
        location_confidence=0.93,
        is_black_sea_region=True,
        confidence=0.91,
        is_new_event=True,
        event_date="2026-09-14",
        incident_time="2026-09-14T08:30:00+03:00",
        reason="A wildfire is explicitly described in the reserve.",
    )

    assert result.location_type == NewsLocationType.protected_area
    assert result.location_confidence == 0.93
    assert result.incident_time == "2026-09-14T08:30:00+03:00"


def test_location_confidence_is_bounded():
    with pytest.raises(ValidationError):
        NewsClassification(
            classification="incident",
            category="wildfire",
            location_name="Novorossiysk",
            location_type="city",
            location_confidence=1.5,
            confidence=0.8,
            reason="Test.",
        )


def test_old_classification_payload_remains_valid():
    result = NewsClassification(
        classification="incident",
        category="wildfire",
        location_name="Novorossiysk",
        is_black_sea_region=True,
        confidence=0.8,
        is_new_event=True,
        event_date=None,
        reason="A wildfire is explicitly described.",
    )

    assert result.location_type is None
    assert result.location_confidence is None
    assert result.incident_time is None


def test_qwen_prompt_keeps_system_owned_metadata_out_of_llm():
    prompt = _build_prompt(
        make_item()
    )

    assert "Do NOT generate latitude or longitude." in prompt
    assert "Do not generate detection_time." in prompt
    assert "Do not generate source_time." in prompt
    assert "Never invent a time." in prompt
    assert "location_confidence" in prompt
