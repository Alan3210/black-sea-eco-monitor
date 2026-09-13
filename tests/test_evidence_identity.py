
from agents.news_agent.event_store import EventStore


def test_existing_evidence_url_returns_event(
    tmp_path,
):

    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Forest fire",
        confidence=0.8,
    )

    store.add_evidence(
        event_id=event_id,
        source="Test",
        title="Fire report",
        url="https://example.com/report",
        published_at=None,
        confidence=0.8,
        reason="Initial report",
    )

    found = store.find_event_by_evidence_url(
        "https://example.com/report"
    )

    assert found == event_id
