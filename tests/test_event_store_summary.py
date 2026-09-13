from agents.news_agent.llm_batch import (
    print_event_store_summary,
)


class FakeEventStore:
    def __init__(
        self,
        events,
    ):
        self.events = events

    def list_event_records(self):
        return self.events


def test_event_store_summary_uses_persisted_events(
    capsys,
):
    store = FakeEventStore(
        [
            {
                "id": "evt_001",
                "category": "wildfire",
                "location": {
                    "name": "Novorossiysk",
                    "latitude": 44.724,
                    "longitude": 37.7691,
                },
                "primary_title": "Test wildfire",
                "status": "resolved",
                "severity": "medium",
                "confidence": 0.9,
                "evidence_count": 4,
            },
            {
                "id": "evt_002",
                "category": "industrial_fire",
                "location": {
                    "name": "Gelendzhik",
                    "latitude": 44.5609,
                    "longitude": 38.0767,
                },
                "primary_title": "Test substation fire",
                "status": "resolved",
                "severity": "medium",
                "confidence": 0.8,
                "evidence_count": 2,
            },
        ]
    )

    print_event_store_summary(
        store
    )

    output = capsys.readouterr().out

    assert "EVENT STORE SUMMARY" in output
    assert "Persisted events: 2" in output
    assert "evt_001" in output
    assert "evt_002" in output
    assert "Evidence count: 4" in output
    assert "44.724, 37.7691" in output
    assert "EVENT CORRELATION" not in output


def test_event_store_summary_handles_empty_store(
    capsys,
):
    store = FakeEventStore(
        []
    )

    print_event_store_summary(
        store
    )

    output = capsys.readouterr().out

    assert "EVENT STORE SUMMARY" in output
    assert "No persisted events." in output
    assert "EVENT CORRELATION" not in output
