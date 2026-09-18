from __future__ import annotations

from typing import Any

from agents.news_agent.event_store import EventStore


def _event_coordinates(
    event: dict[str, Any],
) -> tuple[float | None, float | None]:
    location = event.get("location")

    if not isinstance(location, dict):
        return None, None

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if latitude is None or longitude is None:
        return None, None

    return float(latitude), float(longitude)


def build_monitor_event_context(
    store: EventStore,
    event_id: str,
) -> dict[str, Any] | None:
    event = store.get_event_record(event_id)

    if event is None:
        return None

    evidence = store.get_event_evidence_records(event_id)
    satellite_observations = (
        store.get_event_satellite_observations(event_id)
    )

    latitude, longitude = _event_coordinates(event)
    has_coordinates = (
        latitude is not None
        and longitude is not None
    )

    ocean_drift_href = None

    if has_coordinates:
        ocean_drift_href = (
            "/ocean/drift/"
            f"?lon={longitude}"
            f"&lat={latitude}"
        )

    return {
        "event": event,
        "evidence": evidence,
        "satellite": {
            "count": len(satellite_observations),
            "observations": satellite_observations,
        },
        "readiness": {
            "event_has_coordinates": has_coordinates,
        },
        "capabilities": {
            "ocean_currents": {
                "available": True,
                "method": "GET",
                "href": "/ocean/currents/",
            },
            "ocean_drift": {
                "available": has_coordinates,
                "method": "GET",
                "href": ocean_drift_href,
                "requires_event_coordinates": True,
                "starts_model": True,
            },
            "impact_screening": {
                "available": True,
                "method": "POST",
                "href": "/impact/drift",
                "targets_href": "/impact/targets",
                "requires": [
                    "drift_forecast_payload"
                ],
                "starts_model": False,
            },
            "ar_scene": {
                "available": True,
                "method": "GET",
                "href": "/api/ar/scene",
                "observer_location_is_user_position": True,
            },
        },
        "links": {
            "event": (
                f"/monitor/events/{event_id}"
            ),
            "evidence": (
                f"/monitor/events/{event_id}/evidence"
            ),
            "satellite_observations": (
                f"/monitor/events/{event_id}/"
                "satellite-observations"
            ),
            "satellite_candidates_geojson": (
                "/satellite/observations/"
                "candidates.geojson"
            ),
        },
    }
