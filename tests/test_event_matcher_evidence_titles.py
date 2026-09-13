from agents.news_agent.event_store import EventStore


def test_event_matcher_uses_existing_evidence_titles(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title=(
            "Emergency situation in the "
            "Novorossiysk district"
        ),
        confidence=0.8,
    )

    store.add_evidence(
        event_id=event_id,
        source="Source A",
        title=(
            "Three forest fires are being "
            "extinguished near Dyrso and "
            "Sheskharis"
        ),
        url="https://example.com/first",
        published_at=(
            "2026-09-09T10:00:00+00:00"
        ),
        confidence=0.8,
        reason="Initial evidence.",
    )

    found_event_id = (
        store.find_matching_event(
            category="wildfire",
            location_name="Novorossiysk",
            title=(
                "Firefighters continue "
                "extinguishing forest fires "
                "near Dyrso and Sheskharis"
            ),
        )
    )

    assert found_event_id == event_id


def test_event_titles_include_primary_and_evidence(
    tmp_path,
):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="wildfire",
        location_name="Novorossiysk",
        primary_title="Primary title",
        confidence=0.8,
    )

    store.add_evidence(
        event_id=event_id,
        source="Source A",
        title="Evidence title",
        url="https://example.com/a",
        published_at=None,
        confidence=0.8,
        reason="Evidence A.",
    )

    titles = store.get_event_titles(
        event_id
    )

    assert "Primary title" in titles
    assert "Evidence title" in titles
