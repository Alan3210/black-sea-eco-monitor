from agents.news_agent.classification import (
    NewsClassification,
)
from agents.news_agent.event_metadata import (
    CANONICAL_COORDINATE_SOURCE,
    build_event_store_metadata,
    enrich_existing_event_metadata,
)
from agents.news_agent.models import NewsItem


def make_item():
    return NewsItem(
        title="Wildfire in the reserve",
        url="https://example.com/story",
        source="Test Source",
        published_at="2026-09-14T12:00:00+03:00",
        summary="The wildfire began at 08:30.",
    )


def make_classification():
    return NewsClassification(
        classification="incident",
        category="wildfire",
        location_name="Utrish Reserve",
        location_type="protected_area",
        location_confidence=0.94,
        is_black_sea_region=True,
        confidence=0.91,
        is_new_event=True,
        event_date="2026-09-14",
        incident_time="2026-09-14T08:30:00+03:00",
        reason="A wildfire is explicitly described in the reserve.",
    )


def test_build_event_store_metadata():
    metadata = build_event_store_metadata(
        item=make_item(),
        classification=make_classification(),
        coordinates_resolved=True,
    )

    assert metadata == {
        "location_type": "protected_area",
        "location_confidence": 0.94,
        "coordinate_source": (
            CANONICAL_COORDINATE_SOURCE
        ),
        "incident_time": (
            "2026-09-14T08:30:00+03:00"
        ),
        "source_time": (
            "2026-09-14T12:00:00+03:00"
        ),
    }


def test_coordinate_source_is_null_without_resolved_coordinates():
    metadata = build_event_store_metadata(
        item=make_item(),
        classification=make_classification(),
        coordinates_resolved=False,
    )

    assert metadata["coordinate_source"] is None


class FakeStore:
    def __init__(self):
        self.location_call = None
        self.time_call = None

    def set_event_location_metadata(
        self,
        **kwargs,
    ):
        self.location_call = kwargs
        return True

    def set_event_time_metadata(
        self,
        **kwargs,
    ):
        self.time_call = kwargs
        return False


def test_enrich_existing_event_metadata_uses_non_overwriting_store_methods():
    store = FakeStore()

    changed = enrich_existing_event_metadata(
        event_store=store,
        event_id="evt_123",
        item=make_item(),
        classification=make_classification(),
        coordinates_resolved=True,
    )

    assert changed is True

    assert store.location_call == {
        "event_id": "evt_123",
        "location_type": "protected_area",
        "location_confidence": 0.94,
        "coordinate_source": (
            CANONICAL_COORDINATE_SOURCE
        ),
    }

    assert store.time_call == {
        "event_id": "evt_123",
        "incident_time": (
            "2026-09-14T08:30:00+03:00"
        ),
        "source_time": (
            "2026-09-14T12:00:00+03:00"
        ),
    }


def test_detection_time_is_not_supplied_by_llm_metadata_helper():
    metadata = build_event_store_metadata(
        item=make_item(),
        classification=make_classification(),
        coordinates_resolved=True,
    )

    assert "detection_time" not in metadata
