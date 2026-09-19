from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN = REPO_ROOT / "backend" / "main.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"
FILES = {'backend/api/weather.py': 'from __future__ import annotations\n\nfrom datetime import datetime\nfrom functools import lru_cache\nfrom typing import Annotated\n\nfrom fastapi import APIRouter, Depends, HTTPException, Query\n\nfrom backend.schemas.weather import WeatherPoint\nfrom backend.services.ecmwf_weather_provider import (\n    EcmwfOpenDataWeatherProvider,\n    WeatherProviderError,\n    WeatherSourceUnavailable,\n    WeatherTimeUnavailable,\n)\nfrom backend.services.weather_provider import WeatherProvider\n\n\nrouter = APIRouter(\n    prefix="/weather",\n    tags=["weather"],\n)\n\n\n@lru_cache(maxsize=1)\ndef get_weather_provider() -> WeatherProvider:\n    """\n    Return the process-wide operational weather provider.\n\n    The provider keeps only configuration in memory. GRIB assets are cached\n    on disk by the ECMWF implementation.\n    """\n    return EcmwfOpenDataWeatherProvider()\n\n\n@router.get(\n    "/point",\n    response_model=WeatherPoint,\n    summary="Operational weather at a point",\n)\ndef get_weather_point(\n    latitude: Annotated[\n        float,\n        Query(\n            ge=-90.0,\n            le=90.0,\n            description="Latitude in decimal degrees.",\n        ),\n    ],\n    longitude: Annotated[\n        float,\n        Query(\n            ge=-180.0,\n            le=180.0,\n            description="Longitude in decimal degrees.",\n        ),\n    ],\n    valid_time: Annotated[\n        datetime | None,\n        Query(\n            description=(\n                "Requested UTC-valid time. WEATHER-1.2 currently snaps "\n                "forward to the next available ECMWF model step; the actual "\n                "time used is returned in provenance.valid_time."\n            ),\n        ),\n    ] = None,\n    provider: WeatherProvider = Depends(get_weather_provider),\n) -> WeatherPoint:\n    try:\n        return provider.get_point(\n            latitude=latitude,\n            longitude=longitude,\n            valid_time=valid_time,\n        )\n    except WeatherTimeUnavailable as exc:\n        raise HTTPException(\n            status_code=422,\n            detail=str(exc),\n        ) from exc\n    except WeatherSourceUnavailable as exc:\n        raise HTTPException(\n            status_code=503,\n            detail=str(exc),\n        ) from exc\n    except WeatherProviderError as exc:\n        raise HTTPException(\n            status_code=503,\n            detail=str(exc),\n        ) from exc\n', 'tests/test_weather_api.py': 'from datetime import datetime, timezone\n\nfrom fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\nfrom backend.api.weather import (\n    get_weather_provider,\n    router,\n)\nfrom backend.schemas.weather import (\n    WeatherPoint,\n    WeatherProvenance,\n)\nfrom backend.services.ecmwf_weather_provider import (\n    WeatherSourceUnavailable,\n    WeatherTimeUnavailable,\n)\n\n\nclass FakeWeatherProvider:\n    provider_name = "fake"\n\n    def __init__(self):\n        self.calls = []\n\n    def get_point(\n        self,\n        *,\n        latitude,\n        longitude,\n        valid_time=None,\n    ):\n        self.calls.append(\n            {\n                "latitude": latitude,\n                "longitude": longitude,\n                "valid_time": valid_time,\n            }\n        )\n\n        actual_valid_time = (\n            valid_time\n            if valid_time is not None\n            else datetime(\n                2026,\n                9,\n                19,\n                9,\n                tzinfo=timezone.utc,\n            )\n        )\n\n        return WeatherPoint(\n            latitude=latitude,\n            longitude=longitude,\n            wind_u_10m_ms=-2.0,\n            wind_v_10m_ms=-3.0,\n            wind_speed_10m_ms=3.605551275463989,\n            wind_from_direction_deg=33.690067525979785,\n            precipitation_rate_mm_h=0.2,\n            precipitation_accumulation_mm=1.8,\n            precipitation_interval_start=datetime(\n                2026,\n                9,\n                19,\n                6,\n                tzinfo=timezone.utc,\n            ),\n            precipitation_interval_end=actual_valid_time,\n            provenance=WeatherProvenance(\n                provider="ecmwf",\n                model="ifs",\n                product="open-data-0p25",\n                data_kind="forecast",\n                forecast_reference_time=datetime(\n                    2026,\n                    9,\n                    19,\n                    0,\n                    tzinfo=timezone.utc,\n                ),\n                valid_time=actual_valid_time,\n                retrieved_at=datetime(\n                    2026,\n                    9,\n                    19,\n                    7,\n                    tzinfo=timezone.utc,\n                ),\n                source_uri="google",\n                fallback_used=False,\n            ),\n        )\n\n\ndef make_client(provider):\n    app = FastAPI()\n    app.include_router(router)\n    app.dependency_overrides[\n        get_weather_provider\n    ] = lambda: provider\n    return TestClient(app)\n\n\ndef test_weather_point_endpoint_returns_canonical_contract():\n    provider = FakeWeatherProvider()\n    client = make_client(provider)\n\n    response = client.get(\n        "/weather/point",\n        params={\n            "latitude": 44.6,\n            "longitude": 37.8,\n        },\n    )\n\n    assert response.status_code == 200\n    data = response.json()\n\n    assert data["latitude"] == 44.6\n    assert data["longitude"] == 37.8\n    assert data["wind_u_10m_ms"] == -2.0\n    assert data["wind_v_10m_ms"] == -3.0\n    assert data["provenance"]["provider"] == "ecmwf"\n    assert data["provenance"]["model"] == "ifs"\n    assert data["units"]["wind_speed"] == "m/s"\n\n    assert provider.calls == [\n        {\n            "latitude": 44.6,\n            "longitude": 37.8,\n            "valid_time": None,\n        }\n    ]\n\n\ndef test_weather_point_endpoint_passes_valid_time():\n    provider = FakeWeatherProvider()\n    client = make_client(provider)\n\n    response = client.get(\n        "/weather/point",\n        params={\n            "latitude": 44.6,\n            "longitude": 37.8,\n            "valid_time": "2026-09-19T12:00:00Z",\n        },\n    )\n\n    assert response.status_code == 200\n\n    call = provider.calls[0]\n    assert call["valid_time"] == datetime(\n        2026,\n        9,\n        19,\n        12,\n        tzinfo=timezone.utc,\n    )\n\n\ndef test_weather_point_endpoint_rejects_invalid_coordinates():\n    provider = FakeWeatherProvider()\n    client = make_client(provider)\n\n    response = client.get(\n        "/weather/point",\n        params={\n            "latitude": 100.0,\n            "longitude": 37.8,\n        },\n    )\n\n    assert response.status_code == 422\n    assert provider.calls == []\n\n\ndef test_weather_point_endpoint_maps_time_error_to_422():\n    class Provider(FakeWeatherProvider):\n        def get_point(self, **kwargs):\n            raise WeatherTimeUnavailable(\n                "requested valid time is outside forecast horizon"\n            )\n\n    client = make_client(Provider())\n\n    response = client.get(\n        "/weather/point",\n        params={\n            "latitude": 44.6,\n            "longitude": 37.8,\n        },\n    )\n\n    assert response.status_code == 422\n    assert (\n        "outside forecast horizon"\n        in response.json()["detail"]\n    )\n\n\ndef test_weather_point_endpoint_maps_source_error_to_503():\n    class Provider(FakeWeatherProvider):\n        def get_point(self, **kwargs):\n            raise WeatherSourceUnavailable(\n                "all ECMWF mirrors failed"\n            )\n\n    client = make_client(Provider())\n\n    response = client.get(\n        "/weather/point",\n        params={\n            "latitude": 44.6,\n            "longitude": 37.8,\n        },\n    )\n\n    assert response.status_code == 503\n    assert response.json()["detail"] == "all ECMWF mirrors failed"\n'}

WEATHER_IMPORT = (
    "from backend.api.weather import router as weather_router"
)

IMPORT_CANDIDATES = [
    "from backend.api.impact_registry import router as impact_registry_router",
    "from backend.api.impact import router as impact_router",
]

INCLUDE_CANDIDATES = [
    """app.include_router(
    impact_registry_router
)
""",
    """app.include_router(
    impact_router
)
""",
]


def backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = (
        BACKUP_DIR
        / f"{label}.before_weather1_2_{stamp}{path.suffix}"
    )
    shutil.copy2(path, target)
    return target


def patch_main(text: str) -> str:
    updated = text

    if WEATHER_IMPORT not in updated:
        inserted = False
        for marker in IMPORT_CANDIDATES:
            if marker in updated:
                updated = updated.replace(
                    marker,
                    marker + "\n" + WEATHER_IMPORT,
                    1,
                )
                inserted = True
                break

        if not inserted:
            raise RuntimeError(
                "could not find router import insertion point"
            )

    include_block = """app.include_router(
    weather_router
)
"""

    if include_block not in updated:
        inserted = False
        for marker in INCLUDE_CANDIDATES:
            if marker in updated:
                updated = updated.replace(
                    marker,
                    marker + "\n" + include_block,
                    1,
                )
                inserted = True
                break

        if not inserted:
            raise RuntimeError(
                "could not find router include insertion point"
            )

    return updated


def main() -> int:
    prerequisites = [
        REPO_ROOT / "backend/schemas/weather.py",
        REPO_ROOT / "backend/services/weather_provider.py",
        REPO_ROOT / "backend/services/ecmwf_weather_provider.py",
    ]

    for path in prerequisites:
        if not path.exists():
            print(
                f"ERROR: WEATHER prerequisite missing: {path}"
            )
            return 2

    if not MAIN.exists():
        print(f"ERROR: backend main missing: {MAIN}")
        return 2

    main_text = MAIN.read_text(encoding="utf-8")

    try:
        updated_main = patch_main(main_text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No runtime file was modified.")
        return 3

    backups = []

    if updated_main != main_text:
        backups.append(
            backup(MAIN, "backend_main")
        )

    file_updates = []
    for relative, content in FILES.items():
        path = REPO_ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing == content:
                continue
            backups.append(
                backup(path, path.stem)
            )

        file_updates.append((path, content))

    # Write only after every patch marker has validated.
    if updated_main != main_text:
        MAIN.write_text(
            updated_main,
            encoding="utf-8",
        )

    for path, content in file_updates:
        path.write_text(content, encoding="utf-8")

    print("WEATHER-1.2 Weather API v0.1 installed.")
    print("Modified:")
    print("  backend/main.py")
    print("Created/updated:")
    for relative in FILES:
        print(f"  {relative}")
    print("Endpoint:")
    print("  GET /weather/point")
    print("No OpenDrift/OpenOil or frontend files were modified.")

    if backups:
        print("Backups:")
        for item in backups:
            print(f"  {item.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
