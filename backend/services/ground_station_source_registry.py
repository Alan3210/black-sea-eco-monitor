from __future__ import annotations

from typing import Any


BLACK_SEA_COUNTRIES = {
    "BG": "Bulgaria",
    "RO": "Romania",
    "TR": "Türkiye",
    "GE": "Georgia",
    "UA": "Ukraine",
    "RU": "Russia",
}


GROUND_STATION_SOURCES: dict[str, dict[str, Any]] = {
    "eea": {
        "name": "European Environment Agency Air Quality Download Service",
        "operator": "European Environment Agency",
        "official": True,
        "machine_api": True,
        "api_base": (
            "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
        ),
        "documentation": (
            "https://eeadmz1-downloads-webapp.azurewebsites.net/"
            "content/documentation/How_To_Downloads.pdf"
        ),
        "dataset": "E2a / Up-To-Date unverified station measurements",
        "dataset_id": 1,
        "aggregation": "hour",
        "pollutants": ["PM2.5", "PM10", "NO2", "O3", "SO2", "CO"],
        "black_sea_scope": ["BG", "RO"],
        "role": "primary_station_measurement_source",
        "verification_status": (
            "official API; current country coverage must be checked live"
        ),
        "semantics": {
            "kind": "station_measurement",
            "observation": True,
            "station_measurement": True,
            "model_forecast": False,
            "satellite_observation": False,
            "verification": "E2a is up-to-date/unverified",
        },
    },
    "turkiye_havaizleme": {
        "name": "Ulusal Hava Kalitesi İzleme Ağı",
        "operator": (
            "T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı"
        ),
        "official": True,
        "machine_api": False,
        "portal": "https://www.havaizleme.gov.tr/",
        "black_sea_scope": ["TR"],
        "role": "candidate_local_station_source",
        "verification_status": (
            "official portal publishes hourly raw station data; "
            "stable documented public API not yet validated"
        ),
        "pollutants": ["PM2.5", "PM10", "NO2", "O3", "SO2", "CO"],
    },
    "georgia_airgov": {
        "name": "Georgia Air Quality Portal",
        "operator": "National Environmental Agency of Georgia",
        "official": True,
        "machine_api": False,
        "portal": "https://air.gov.ge/en/",
        "black_sea_scope": ["GE"],
        "role": "candidate_local_station_source",
        "verification_status": (
            "official portal provides continuous automatic-station data; "
            "stable documented public API not yet validated"
        ),
        "pollutants": ["PM2.5", "PM10", "NO2", "O3", "SO2", "CO"],
        "known_black_sea_city": "Batumi",
    },
    "ukraine_open_data": {
        "name": "Ukraine official environmental open data",
        "operator": (
            "Data.gov.ua / Ministry of Environment / Hydrometeorological service"
        ),
        "official": True,
        "machine_api": "partial",
        "portal": "https://data.gov.ua/",
        "black_sea_scope": ["UA"],
        "role": "secondary_station_source_candidate",
        "verification_status": (
            "official daily/monthly datasets exist; a stable near-real-time "
            "Black Sea station feed is not yet validated"
        ),
    },
    "russia_official_monitoring": {
        "name": "Russian official environmental monitoring",
        "operator": "Roshydromet / regional monitoring systems",
        "official": True,
        "machine_api": False,
        "black_sea_scope": ["RU"],
        "role": "pending_local_source",
        "verification_status": (
            "monitoring exists, including Krasnodar Krai, but no stable "
            "public documented near-real-time machine API has been validated"
        ),
    },
}


def primary_black_sea_station_source(country_code: str) -> str | None:
    code = country_code.strip().upper()
    for source_id, source in GROUND_STATION_SOURCES.items():
        if (
            source.get("role") == "primary_station_measurement_source"
            and code in source.get("black_sea_scope", [])
        ):
            return source_id
    return None
