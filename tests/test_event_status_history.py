from agents.news_agent.event_store import EventStore


def test_status_transition_history(tmp_path):

    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Forest fire",
        confidence=0.8,
    )

    result = store.update_status(
        event_id=event_id,
        new_status="active",
        reason="Lifecycle marker detected",
    )

    history = store.get_status_history(
        event_id
    )

    assert result is not None
    assert len(history) == 1
    assert history[0][1] == "active"


def test_same_status_not_added(tmp_path):

    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Forest fire",
        confidence=0.8,
    )

    result = store.update_status(
        event_id=event_id,
        new_status="detected",
        reason="No transition",
    )

    assert result is None
