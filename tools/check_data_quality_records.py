import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.news_agent.event_store import EventStore


def fmt(value):
    return "NULL" if value is None else str(value)


def main():
    store = EventStore()
    events = store.list_event_records()

    print("DATA QUALITY V1 — EVENT STORE CHECK")
    print(f"Database: {store.db_path}")
    print(f"Events: {len(events)}")
    print()

    populated_location_quality = 0
    populated_incident_time = 0
    populated_source_time = 0

    for index, event in enumerate(events, start=1):
        location = event.get("location") or {}
        time_meta = event.get("time") or {}

        location_type = location.get("type")
        location_confidence = location.get("confidence")
        coordinate_source = location.get("source")
        incident_time = time_meta.get("incident_time")
        detection_time = time_meta.get("detection_time")
        source_time = time_meta.get("source_time")

        if any(
            value is not None
            for value in (
                location_type,
                location_confidence,
                coordinate_source,
            )
        ):
            populated_location_quality += 1

        if incident_time is not None:
            populated_incident_time += 1

        if source_time is not None:
            populated_source_time += 1

        print(f"Event #{index}")
        print(f"  ID: {event.get('id')}")
        print(f"  Category: {event.get('category')}")
        print(f"  Location: {location.get('name')}")
        print(f"  Location type: {fmt(location_type)}")
        print(f"  Location confidence: {fmt(location_confidence)}")
        print(f"  Coordinate source: {fmt(coordinate_source)}")
        print(f"  Incident time: {fmt(incident_time)}")
        print(f"  Detection time: {fmt(detection_time)}")
        print(f"  Source time: {fmt(source_time)}")
        print(f"  Evidence count: {event.get('evidence_count', 0)}")
        print()

    print("SUMMARY")
    print(
        "  Events with location-quality metadata: "
        f"{populated_location_quality}/{len(events)}"
    )
    print(
        "  Events with incident_time: "
        f"{populated_incident_time}/{len(events)}"
    )
    print(
        "  Events with source_time: "
        f"{populated_source_time}/{len(events)}"
    )


if __name__ == "__main__":
    main()
