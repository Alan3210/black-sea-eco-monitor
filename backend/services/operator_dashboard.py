from __future__ import annotations

from typing import Any

from agents.news_agent.event_store import EventStore


def _effective_event_time(
    event: dict[str, Any],
) -> str | None:
    time_data = event.get("time")

    if not isinstance(time_data, dict):
        return None

    return (
        time_data.get("incident_time")
        or time_data.get("source_time")
        or time_data.get("detection_time")
    )


def _has_coordinates(
    event: dict[str, Any],
) -> bool:
    location = event.get("location")

    if not isinstance(location, dict):
        return False

    return (
        location.get("latitude") is not None
        and location.get("longitude") is not None
    )


def build_operator_event_row(
    store: EventStore,
    event: dict[str, Any],
) -> dict[str, Any]:
    event_id = event["id"]
    location = event.get("location") or {}
    has_coordinates = _has_coordinates(event)

    satellite_count = len(
        store.get_event_satellite_observations(
            event_id
        )
    )

    location_name = (
        location.get("name")
        or "Unknown location"
    )

    category = (
        event.get("category")
        or "unknown"
    )

    return {
        "id": event_id,
        "display_label": (
            f"{location_name} · {category}"
        ),
        "primary_title": event.get(
            "primary_title"
        ),
        "category": category,
        "status": event.get("status"),
        "severity": event.get("severity"),
        "confidence": event.get("confidence"),
        "location": {
            "name": location.get("name"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "type": location.get("type"),
        },
        "event_time": _effective_event_time(
            event
        ),
        "updated_at": event.get(
            "updated_at"
        ),
        "evidence_count": int(
            event.get("evidence_count")
            or 0
        ),
        "satellite_count": satellite_count,
        "readiness": {
            "has_coordinates": has_coordinates,
            "ocean_drift": has_coordinates,
            "impact_after_drift": has_coordinates,
            "ar_scene": True,
        },
        "links": {
            "event": (
                f"/monitor/events/{event_id}"
            ),
            "context": (
                f"/monitor/events/{event_id}/context"
            ),
            "evidence": (
                f"/monitor/events/{event_id}/evidence"
            ),
            "satellite_observations": (
                f"/monitor/events/{event_id}/"
                "satellite-observations"
            ),
        },
    }


def build_operator_dashboard(
    store: EventStore,
    *,
    status: str | None = None,
    category: str | None = None,
    has_coordinates: bool | None = None,
) -> dict[str, Any]:
    rows = []

    for event in store.list_event_records():
        if (
            status is not None
            and event.get("status") != status
        ):
            continue

        if (
            category is not None
            and event.get("category") != category
        ):
            continue

        row = build_operator_event_row(
            store,
            event,
        )

        if (
            has_coordinates is not None
            and row["readiness"][
                "has_coordinates"
            ]
            is not has_coordinates
        ):
            continue

        rows.append(row)

    return {
        "count": len(rows),
        "items": rows,
        "semantics": {
            "read_model": "operator_dashboard",
            "heavy_models_started": False,
            "impact_after_drift": (
                "workflow readiness only; "
                "no impact forecast is computed here"
            ),
        },
    }
