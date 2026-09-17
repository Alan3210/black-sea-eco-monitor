import sqlite3

import pytest

from agents.news_agent.event_store import EventStore


def _create_observation(
    store,
    *,
    acquisition_time="2026-09-17T03:31:58Z",
    confidence=0.72,
):
    return store.create_satellite_observation(
        observation_type="sar_scene",
        sensor="Sentinel-1",
        platform="D",
        dataset_id="COPERNICUS/S1_GRD",
        source_image_id="S1D_TEST_SCENE",
        acquisition_time=acquisition_time,
        processing_time="2026-09-17T18:32:38Z",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [
                    [37.0, 42.8],
                    [40.4, 42.8],
                    [40.4, 44.7],
                    [37.0, 44.7],
                    [37.0, 42.8],
                ]
            ],
        },
        bbox_min_lon=37.0,
        bbox_min_lat=42.8,
        bbox_max_lon=40.4,
        bbox_max_lat=44.7,
        confidence=confidence,
        review_status="unreviewed",
        processing_version="0.1",
        provenance={
            "data_provider": "Copernicus Sentinel-1",
            "processing_platform": "Google Earth Engine",
        },
    )


def test_create_and_get_satellite_observation_round_trip(tmp_path):
    store = EventStore(tmp_path / "events.db")

    observation_id = _create_observation(store)

    observation = store.get_satellite_observation(
        observation_id
    )

    assert observation["id"] == observation_id
    assert observation["information_type"] == "satellite_observation"
    assert observation["derivation_level"] == "processed"
    assert observation["observation_type"] == "sar_scene"
    assert observation["sensor"] == "Sentinel-1"
    assert observation["platform"] == "D"
    assert observation["dataset_id"] == "COPERNICUS/S1_GRD"
    assert observation["source_image_id"] == "S1D_TEST_SCENE"
    assert observation["acquisition_time"] == "2026-09-17T03:31:58+00:00"
    assert observation["processing_time"] == "2026-09-17T18:32:38+00:00"
    assert observation["confidence"] == 0.72
    assert observation["review_status"] == "unreviewed"
    assert observation["bbox"] == {
        "min_lon": 37.0,
        "min_lat": 42.8,
        "max_lon": 40.4,
        "max_lat": 44.7,
    }
    assert observation["geometry"]["type"] == "Polygon"
    assert observation["provenance"]["processing_platform"] == (
        "Google Earth Engine"
    )


def test_get_satellite_observation_returns_none_for_missing_id(tmp_path):
    store = EventStore(tmp_path / "events.db")

    assert store.get_satellite_observation(
        "satobs_missing"
    ) is None


def test_list_satellite_observations_orders_by_acquisition_time_desc(tmp_path):
    store = EventStore(tmp_path / "events.db")

    older_id = _create_observation(
        store,
        acquisition_time="2026-09-16T03:31:58Z",
    )

    newer_id = store.create_satellite_observation(
        observation_type="sar_scene",
        sensor="Sentinel-1",
        dataset_id="COPERNICUS/S1_GRD",
        source_image_id="S1D_TEST_SCENE_NEWER",
        acquisition_time="2026-09-17T03:31:58Z",
    )

    observations = store.list_satellite_observations()

    assert [
        item["id"]
        for item in observations
    ] == [
        newer_id,
        older_id,
    ]


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("derivation_level", "forecast"),
        ("review_status", "confirmed_oil"),
    ],
)
def test_satellite_observation_rejects_invalid_enum(
    tmp_path,
    field_name,
    field_value,
):
    store = EventStore(tmp_path / "events.db")

    kwargs = {
        "observation_type": "sar_scene",
        "sensor": "Sentinel-1",
        "dataset_id": "COPERNICUS/S1_GRD",
        "source_image_id": "S1D_TEST_SCENE",
        "acquisition_time": "2026-09-17T03:31:58Z",
        field_name: field_value,
    }

    with pytest.raises(ValueError):
        store.create_satellite_observation(
            **kwargs
        )


def test_satellite_observation_rejects_invalid_confidence(tmp_path):
    store = EventStore(tmp_path / "events.db")

    with pytest.raises(ValueError):
        _create_observation(
            store,
            confidence=1.5,
        )


def test_satellite_observation_requires_valid_acquisition_time(tmp_path):
    store = EventStore(tmp_path / "events.db")

    with pytest.raises(ValueError):
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1D_TEST_SCENE",
            acquisition_time="not-a-datetime",
        )


def test_satellite_observation_requires_complete_bbox(tmp_path):
    store = EventStore(tmp_path / "events.db")

    with pytest.raises(ValueError):
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1D_TEST_SCENE",
            acquisition_time="2026-09-17T03:31:58Z",
            bbox_min_lon=37.0,
        )


def test_satellite_observation_rejects_invalid_bbox_range(tmp_path):
    store = EventStore(tmp_path / "events.db")

    with pytest.raises(ValueError):
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1D_TEST_SCENE",
            acquisition_time="2026-09-17T03:31:58Z",
            bbox_min_lon=40.4,
            bbox_min_lat=42.8,
            bbox_max_lon=37.0,
            bbox_max_lat=44.7,
        )


def test_satellite_observation_requires_dict_json_fields(tmp_path):
    store = EventStore(tmp_path / "events.db")

    with pytest.raises(ValueError):
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1D_TEST_SCENE",
            acquisition_time="2026-09-17T03:31:58Z",
            geometry=[],
        )

    with pytest.raises(ValueError):
        store.create_satellite_observation(
            observation_type="sar_scene",
            sensor="Sentinel-1",
            dataset_id="COPERNICUS/S1_GRD",
            source_image_id="S1D_TEST_SCENE",
            acquisition_time="2026-09-17T03:31:58Z",
            provenance=[],
        )


def test_link_satellite_observation_to_event_is_idempotent(tmp_path):
    db_path = tmp_path / "events.db"
    store = EventStore(db_path)

    event_id = store.create_event(
        category="possible_pollution",
        location_name="Novorossiysk",
        primary_title="Possible pollution near Novorossiysk",
    )
    observation_id = _create_observation(store)

    first_result = store.link_satellite_observation_to_event(
        event_id=event_id,
        satellite_observation_id=observation_id,
        relation_type="spatial_overlap",
        relation_confidence=0.8,
    )

    second_result = store.link_satellite_observation_to_event(
        event_id=event_id,
        satellite_observation_id=observation_id,
        relation_type="spatial_overlap",
        relation_confidence=0.8,
    )

    assert first_result is True
    assert second_result is False

    with sqlite3.connect(db_path) as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM event_satellite_observations
            WHERE event_id = ?
              AND satellite_observation_id = ?
            """,
            (
                event_id,
                observation_id,
            ),
        ).fetchone()[0]

    assert count == 1


def test_link_rejects_missing_event(tmp_path):
    store = EventStore(tmp_path / "events.db")
    observation_id = _create_observation(store)

    with pytest.raises(
        ValueError,
        match="event not found",
    ):
        store.link_satellite_observation_to_event(
            event_id="evt_missing",
            satellite_observation_id=observation_id,
            relation_type="contextual",
        )


def test_link_rejects_missing_satellite_observation(tmp_path):
    store = EventStore(tmp_path / "events.db")

    event_id = store.create_event(
        category="possible_pollution",
        location_name="Novorossiysk",
        primary_title="Possible pollution near Novorossiysk",
    )

    with pytest.raises(
        ValueError,
        match="satellite observation not found",
    ):
        store.link_satellite_observation_to_event(
            event_id=event_id,
            satellite_observation_id="satobs_missing",
            relation_type="contextual",
        )


def test_link_rejects_invalid_relation_type(tmp_path):
    store = EventStore(tmp_path / "events.db")

    event_id = store.create_event(
        category="possible_pollution",
        location_name="Novorossiysk",
        primary_title="Possible pollution near Novorossiysk",
    )
    observation_id = _create_observation(store)

    with pytest.raises(ValueError):
        store.link_satellite_observation_to_event(
            event_id=event_id,
            satellite_observation_id=observation_id,
            relation_type="confirmed_causation",
        )


def test_link_does_not_modify_event_lifecycle_timestamps(tmp_path):
    store = EventStore(tmp_path / "events.db")

    event_id = store.create_event(
        category="possible_pollution",
        location_name="Novorossiysk",
        primary_title="Possible pollution near Novorossiysk",
    )
    observation_id = _create_observation(store)

    before = store.get_event_record(event_id)

    store.link_satellite_observation_to_event(
        event_id=event_id,
        satellite_observation_id=observation_id,
        relation_type="contextual",
    )

    after = store.get_event_record(event_id)

    assert after["last_seen"] == before["last_seen"]
    assert after["updated_at"] == before["updated_at"]
