from backend.services.ground_station_source_registry import GROUND_STATION_SOURCES
from backend.services.eea_station_refresh_service import (
    refresh_eea_station_observations,
)


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


def get_station_observations(source="eea"):
    if source == "eea":
        result = refresh_eea_station_observations()

        return {
            "source": source,
            "stations": [],
            "status": "provider_connected",
            "refresh": result,
        }

    return {
        "source": source,
        "stations": [],
        "status": "provider_not_connected",
    }
