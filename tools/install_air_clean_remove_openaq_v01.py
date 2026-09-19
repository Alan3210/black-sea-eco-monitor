from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".air_clean_payload"
BACKUP_ROOT = REPO_ROOT / "dev-snapshots"

REMOVE_FILES = [
    "backend/services/openaq_client.py",
    "backend/cache/air_quality_cache.py",
    "backend/services/air_quality.py",
    "backend/api/air_quality.py",
    "tests/test_air_quality_service.py",
    "tests/test_air_quality_api.py",
    "tests/test_air_quality_live_cache.py",
    "tests/test_air_quality_router_registration.py",
    "README_AIR1_0_OPENAQ_API_V01.txt",
    "README_AIR1_1_OPENAQ_LIVE_CACHE_V01.txt",
    "README_AIR1_1_FIX.txt",
    "README_AIR1_1_FIX2.txt",
    "README_AIR1_1_1_ROUTER_REGISTRATION_FIX_V01.txt",
    "README_AIR1_1_1_FIX2_ROUTER_TEST_V01.txt",
    "README_AIR1_2_WEBGIS_AIR_QUALITY_LAYER_V01.txt",
    "README_AIR1_2_1_WEBGIS_AIR_STATIONS_V01.txt",
    "tools/install_air1_0_openaq_api_v01.py",
    "tools/install_air1_1_openaq_live_cache_v01.py",
    "tools/install_air1_1_fix_preserve_air1_api_v01.py",
    "tools/install_air1_1_fix2_preserve_all_air1_api_v01.py",
    "tools/install_air1_1_1_router_registration_fix_v01.py",
    "tools/install_air1_1_1_fix2_router_test_v01.py",
    "tools/install_air1_2_webgis_air_quality_layer_v01.py",
    "tools/install_air1_2_1_webgis_air_stations_v01.py"
]

NEUTRAL_FRONTEND = [
    "frontend/src/airQuality.js",
    "frontend/src/airQuality.test.js",
    "frontend/src/airLayer.js",
    "frontend/src/airLayer.test.js",
]

AIR_IMPORT = (
    "from backend.api.air_quality "
    "import router as air_quality_router"
)

AIR_INCLUDE = (
    "app.include_router(air_quality_router)"
)


def main() -> int:
    main_path = (
        REPO_ROOT
        / "backend"
        / "main.py"
    )

    if not main_path.exists():
        print(
            "ERROR: backend/main.py not found."
        )
        return 2

    missing_payload = [
        rel
        for rel in NEUTRAL_FRONTEND
        if not (
            PAYLOAD_ROOT / rel
        ).exists()
    ]

    if missing_payload:
        print(
            "ERROR: AIR-CLEAN payload is incomplete:"
        )
        for rel in missing_payload:
            print(
                f"  {rel}"
            )
        return 3

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    snapshot = (
        BACKUP_ROOT
        / f"air-clean-{stamp}"
    )

    snapshot.mkdir(
        parents=True,
        exist_ok=False,
    )

    changed = []

    def backup(rel: str) -> None:
        source = REPO_ROOT / rel
        if not source.exists():
            return

        target = snapshot / rel
        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            target,
        )

    # Backup backend/main.py before route cleanup.
    backup(
        "backend/main.py"
    )

    # Backup all files that will be deleted.
    for rel in REMOVE_FILES:
        backup(rel)

    # Backup frontend helpers that will be neutralized.
    for rel in NEUTRAL_FRONTEND:
        backup(rel)

    # Remove AIR router registration while preserving all other routers.
    text = main_path.read_text(
        encoding="utf-8",
    )

    lines = text.splitlines()

    filtered = [
        line
        for line in lines
        if line.strip() not in {
            AIR_IMPORT,
            AIR_INCLUDE,
        }
    ]

    updated = "\n".join(
        filtered
    ).rstrip() + "\n"

    main_path.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    changed.append(
        "backend/main.py"
    )

    # Delete abandoned OpenAQ files.
    removed = []

    for rel in REMOVE_FILES:
        path = REPO_ROOT / rel

        if path.exists():
            path.unlink()
            removed.append(rel)

    # Remove empty backend/cache directory if AIR-1.1 created it and
    # there are no other files there.
    cache_dir = (
        REPO_ROOT
        / "backend"
        / "cache"
    )

    if (
        cache_dir.exists()
        and cache_dir.is_dir()
        and not any(
            cache_dir.iterdir()
        )
    ):
        cache_dir.rmdir()

    # Install provider-neutral observation helpers for future EEA /
    # regional station sources.
    for rel in NEUTRAL_FRONTEND:
        source = PAYLOAD_ROOT / rel
        target = REPO_ROOT / rel

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            target,
        )

        changed.append(rel)

    shutil.rmtree(
        PAYLOAD_ROOT,
    )

    print(
        "AIR-CLEAN Remove OpenAQ v0.1 installed."
    )
    print(
        "Removed OpenAQ runtime/API/tests/history files:",
        len(removed),
    )
    print(
        "Removed FastAPI route: /air/quality"
    )
    print(
        "Preserved provider-neutral ground-observation frontend helpers."
    )
    print(
        "Snapshot:",
        snapshot,
    )
    print(
        "No ECMWF, Copernicus, OpenDrift, Impact, Satellite, or EventStore code modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
