from agents.news_agent.event_store import EventStore


def test_create_and_find_event(tmp_path):

    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Лесной пожар под Новороссийском",
        confidence=0.8,
    )

    found = store.find_matching_event(
        category="wildfire",
        location_name="Novorossiysk",
        title="Лесной пожар под Новороссийском",
    )

    assert found == event_id


def test_add_evidence_updates_event(tmp_path):

    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="industrial_fire",
        location_name="Novorossiysk",
        primary_title="Пожар на терминале",
        confidence=0.8,
    )

    evidence_id = store.add_evidence(
        event_id=event_id,
        source="Test",
        title="Terminal fire",
        url=None,
        published_at=None,
        confidence=0.8,
        reason="Confirmed fire.",
    )

    evidence = store.get_event_evidence(
        event_id
    )

    assert evidence_id is not None
    assert len(evidence) == 1
