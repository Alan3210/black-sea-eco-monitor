from agents.news_agent.event_store import EventStore


def test_status_does_not_move_backwards(tmp_path):

    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Forest fire",
        confidence=0.8,
    )

    store.update_status(
        event_id=event_id,
        new_status="active",
        reason="Fire is active.",
    )

    store.update_status(
        event_id=event_id,
        new_status="contained",
        reason="Fire contained.",
    )

    store.update_status(
        event_id=event_id,
        new_status="resolved",
        reason="Fire resolved.",
    )

    result = store.update_status(
        event_id=event_id,
        new_status="active",
        reason="Older active report arrived later.",
    )

    history = store.get_status_history(
        event_id
    )

    assert result is None
    assert [row[1] for row in history] == [
        "active",
        "contained",
        "resolved",
    ]
