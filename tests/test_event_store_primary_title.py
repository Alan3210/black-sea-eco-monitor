from agents.news_agent.event_store import EventStore


def test_match_uses_primary_title(tmp_path):

    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title=(
            "Лесной пожар под Новороссийском"
        ),
        confidence=0.8,
    )

    found = store.find_matching_event(
        category="wildfire",
        location_name="Novorossiysk",
        title=(
            "Три лесных пожара тушат "
            "под Новороссийском"
        ),
    )

    assert found == event_id
