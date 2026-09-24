from pathlib import Path
import json
import requests

EEA_URLS_ENDPOINT = (
    "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
    "/ParquetFile/urls"
)

def discover_eea_parquet_urls(
    countries=("BG", "RO"),
    pollutants=None,
    session=None,
):
    session = session or requests.Session()

    payload = {
        "countries": list(countries),
        "cities": [],
        "pollutants": pollutants or [],
        "dataset": 1,
        "aggregationType": "hour",
    }

    response = session.post(
        EEA_URLS_ENDPOINT,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    urls = [
        line.strip()
        for line in response.text.splitlines()
        if line.strip() and "ParquetFileUrl" not in line
    ]

    return urls


def save_eea_parquet_urls(urls, path="data/cache/air/eea-stations/urls.json"):
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        json.dumps(urls, indent=2),
        encoding="utf-8",
    )
