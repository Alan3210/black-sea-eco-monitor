from agents.news_agent.event_store import EventStore


def _create_store_and_event(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Forest fire",
        confidence=0.8,
    )

    return store, event_id


def test_duplicate_evidence_url_is_not_added_twice(
    tmp_path,
):
    store, event_id = _create_store_and_event(
        tmp_path
    )

    first_id = store.add_evidence(
        event_id=event_id,
        source="Example News",
        title="Wildfire near Novorossiysk",
        url="https://example.com/fire-1",
        published_at="2026-09-09T10:00:00+00:00",
        confidence=0.8,
        reason="First report.",
    )

    second_id = store.add_evidence(
        event_id=event_id,
        source="Example News",
        title="Wildfire near Novorossiysk",
        url="https://example.com/fire-1",
        published_at="2026-09-09T10:00:00+00:00",
        confidence=0.8,
        reason="Same report again.",
    )

    evidence = store.get_event_evidence(
        event_id
    )

    assert first_id == second_id
    assert len(evidence) == 1


def test_duplicate_without_url_uses_source_and_title(
    tmp_path,
):
    store, event_id = _create_store_and_event(
        tmp_path
    )

    first_id = store.add_evidence(
        event_id=event_id,
        source="Local Source",
        title="Fire has been contained",
        url=None,
        published_at="2026-09-09T12:00:00+00:00",
        confidence=0.9,
        reason="Follow-up.",
    )

    second_id = store.add_evidence(
        event_id=event_id,
        source="Local Source",
        title="Fire has been contained",
        url=None,
        published_at="2026-09-09T12:00:00+00:00",
        confidence=0.9,
        reason="Repeated follow-up.",
    )

    evidence = store.get_event_evidence(
        event_id
    )

    assert first_id == second_id
    assert len(evidence) == 1
