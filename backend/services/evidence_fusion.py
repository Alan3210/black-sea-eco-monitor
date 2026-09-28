from __future__ import annotations

from typing import Any

from agents.news_agent.event_store import EventStore
from backend.schemas.investigation_evidence import (
    CanonicalEvidenceRecord,
    InvestigationEvidenceBundle,
)


def normalize_source_evidence(
    record: dict[str, Any],
) -> CanonicalEvidenceRecord:
    return CanonicalEvidenceRecord(
        id=record["id"],
        event_id=record["event_id"],
        evidence_type="source_report",
        source=record.get("source"),
        timestamp=(
            record.get("published_at")
            or record.get("created_at")
        ),
        confidence=record.get("confidence"),
        title=record.get("title"),
        metadata={
            "reason": record.get("reason"),
        },
        provenance={
            "url": record.get("url"),
            "published_at": record.get(
                "published_at"
            ),
            "created_at": record.get(
                "created_at"
            ),
        },
    )


def normalize_satellite_evidence(
    event_id: str,
    record: dict[str, Any],
) -> CanonicalEvidenceRecord:
    observation = record["observation"]

    return CanonicalEvidenceRecord(
        id=observation["id"],
        event_id=event_id,
        evidence_type="satellite_observation",
        source=(
            observation.get("sensor")
            or observation.get("platform")
        ),
        timestamp=observation.get(
            "acquisition_time"
        ),
        confidence=observation.get("confidence"),
        title=observation.get(
            "observation_type"
        ),
        metadata={
            "information_type": observation.get(
                "information_type"
            ),
            "derivation_level": observation.get(
                "derivation_level"
            ),
            "review_status": observation.get(
                "review_status"
            ),
            "bbox": {
                "min_lon": observation.get(
                    "bbox_min_lon"
                ),
                "min_lat": observation.get(
                    "bbox_min_lat"
                ),
                "max_lon": observation.get(
                    "bbox_max_lon"
                ),
                "max_lat": observation.get(
                    "bbox_max_lat"
                ),
            },
            "relation_type": record.get(
                "relation_type"
            ),
            "relation_confidence": record.get(
                "relation_confidence"
            ),
        },
        provenance={
            "dataset_id": observation.get(
                "dataset_id"
            ),
            "source_image_id": observation.get(
                "source_image_id"
            ),
            "sensor": observation.get("sensor"),
            "platform": observation.get(
                "platform"
            ),
            "processing_time": observation.get(
                "processing_time"
            ),
            "processing_version": observation.get(
                "processing_version"
            ),
            "processing_method": observation.get(
                "processing_method"
            ),
            "provenance_json": observation.get(
                "provenance_json"
            ),
            "link_created_at": record.get(
                "created_at"
            ),
        },
    )


def build_event_investigation_evidence(
    store: EventStore,
    event_id: str,
) -> InvestigationEvidenceBundle | None:
    event = store.get_event_record(event_id)

    if event is None:
        return None

    evidence = [
        normalize_source_evidence(record)
        for record in store.get_event_evidence_records(
            event_id
        )
    ]

    evidence.extend(
        normalize_satellite_evidence(
            event_id,
            record,
        )
        for record in (
            store.get_event_satellite_observations(
                event_id
            )
        )
    )

    return InvestigationEvidenceBundle(
        event_id=event_id,
        evidence=evidence,
    )