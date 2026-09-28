from agents.news_agent.event_store import EventStore
from backend.services.evidence_fusion import (
    build_event_investigation_evidence,
)


def _build_store(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    event_id = store.create_event(
        category="oil_spill",
        location_name="Novorossiysk",
        primary_title="Test oil spill",
        latitude=44.724,
        longitude=37.7691,
    )

    store.add_evidence(
        event_id=event_id,
        source="Test Source",
        title="Oil spill report",
        url="https://example.com/report",
        published_at=(
            "2026-09-28T10:15:00+00:00"
        ),
        confidence=0.8,
        reason="Initial source report",
    )

    observation_id = (
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            platform="D",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1_TEST_SCENE",
            acquisition_time=(
                "2026-09-28T10:30:00Z"
            ),
            confidence=0.9,
            processing_version="0.1",
        )
    )

    store.link_satellite_observation_to_event(
        event_id=event_id,
        satellite_observation_id=observation_id,
        relation_type="spatial_overlap",
        relation_confidence=0.75,
    )

    return store, event_id, observation_id


def test_builds_canonical_evidence_from_existing_store(
    tmp_path,
):
    store, event_id, observation_id = (
        _build_store(tmp_path)
    )

    result = build_event_investigation_evidence(
        store,
        event_id,
    )

    assert result is not None
    assert result.event_id == event_id
    assert len(result.evidence) == 2
    assert result.candidate_sources == []

    source_record = result.evidence[0]

    assert source_record.evidence_type == (
        "source_report"
    )
    assert source_record.source == "Test Source"
    assert source_record.confidence == 0.8
    assert source_record.provenance["url"] == (
        "https://example.com/report"
    )

    satellite_record = result.evidence[1]

    assert satellite_record.id == observation_id
    assert satellite_record.evidence_type == (
        "satellite_observation"
    )
    assert satellite_record.source == "Sentinel-1"
    assert satellite_record.confidence == 0.9
    assert satellite_record.metadata[
        "relation_confidence"
    ] == 0.75
    assert satellite_record.provenance[
        "dataset_id"
    ] == "COPERNICUS/S1_GRD"


def test_missing_event_returns_none(tmp_path):
    store = EventStore(
        tmp_path / "events.db"
    )

    result = build_event_investigation_evidence(
        store,
        "evt_missing",
    )

    assert result is None