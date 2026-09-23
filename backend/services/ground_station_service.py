from backend.services.ground_station_source_registry import GROUND_STATION_SOURCES

def get_station_sources():
    return [
        {
            "id": key,
            "name": value["name"],
            "role": value["role"],
            "semantics": value.get("semantics", {}),
        }
        for key, value in GROUND_STATION_SOURCES.items()
    ]

def get_station_observations():
    return {
        "stations": [],
        "status": "provider_not_connected",
    }
