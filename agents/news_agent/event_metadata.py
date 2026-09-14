CANONICAL_COORDINATE_SOURCE = "canonical_database"


def _enum_value(value):
    if value is None:
        return None

    return getattr(
        value,
        "value",
        value,
    )


def build_event_store_metadata(
    *,
    item,
    classification,
    coordinates_resolved,
):
    return {
        "location_type": _enum_value(
            getattr(
                classification,
                "location_type",
                None,
            )
        ),
        "location_confidence": getattr(
            classification,
            "location_confidence",
            None,
        ),
        "coordinate_source": (
            CANONICAL_COORDINATE_SOURCE
            if coordinates_resolved
            else None
        ),
        "incident_time": getattr(
            classification,
            "incident_time",
            None,
        ),
        "source_time": getattr(
            item,
            "published_at",
            None,
        ),
    }


def enrich_existing_event_metadata(
    *,
    event_store,
    event_id,
    item,
    classification,
    coordinates_resolved,
):
    metadata = build_event_store_metadata(
        item=item,
        classification=classification,
        coordinates_resolved=coordinates_resolved,
    )

    location_changed = (
        event_store.set_event_location_metadata(
            event_id=event_id,
            location_type=metadata["location_type"],
            location_confidence=(
                metadata["location_confidence"]
            ),
            coordinate_source=(
                metadata["coordinate_source"]
            ),
        )
    )

    time_changed = (
        event_store.set_event_time_metadata(
            event_id=event_id,
            incident_time=metadata["incident_time"],
            source_time=metadata["source_time"],
        )
    )

    return (
        location_changed
        or time_changed
    )
