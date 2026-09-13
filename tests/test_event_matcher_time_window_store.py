from agents.news_agent.event_store import EventStore


def _create_event_with_evidence(
    store,
    *,
    title,
    published_at,
):
    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title=title,
        confidence=0.8,
    )

    store.add_evidence(
        event_id=event_id,
        source="Test Source",
        title=title,
        url=(
            "https://example.com/"
            + event_id
        ),
        published_at=published_at,
        confidence=0.8,
        reason="Test evidence.",
    )

    return event_id


def test_matcher_accepts_event_inside_72_hour_window(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = _create_event_with_evidence(
        store,
        title="Wildfire near Novorossiysk",
        published_at=(
            "Wed, 09 Sep 2026 "
            "10:00:00 GMT"
        ),
    )

    found = store.find_matching_event(
        category="wildfire",
        location_name="Novorossiysk",
        title="Wildfire near Novorossiysk",
        published_at=(
            "Fri, 11 Sep 2026 "
            "10:00:00 GMT"
        ),
    )

    assert found == event_id


def test_matcher_rejects_event_outside_72_hour_window(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    _create_event_with_evidence(
        store,
        title="Wildfire near Novorossiysk",
        published_at=(
            "Tue, 01 Sep 2026 "
            "10:00:00 GMT"
        ),
    )

    found = store.find_matching_event(
        category="wildfire",
        location_name="Novorossiysk",
        title="Wildfire near Novorossiysk",
        published_at=(
            "Sat, 05 Sep 2026 "
            "10:00:01 GMT"
        ),
    )

    assert found is None
