from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN = REPO_ROOT / "backend" / "main.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

IMPORT_LINE = (
    "from backend.api.wind_field import "
    "router as wind_field_router\n"
)
INCLUDE_BLOCK = """app.include_router(
    wind_field_router
)


"""


def backup_main() -> Path:
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    target = (
        BACKUP_DIR
        / f"main.before_weather1_5a_{stamp}.py"
    )
    shutil.copy2(
        MAIN,
        target,
    )
    return target


def patch_main(text: str) -> str:
    updated = text

    if IMPORT_LINE not in updated:
        anchor = (
            "from fastapi import FastAPI\n"
        )

        if anchor not in updated:
            raise RuntimeError(
                "backend/main.py FastAPI import marker not found"
            )

        updated = updated.replace(
            anchor,
            anchor
            + "\n"
            + IMPORT_LINE,
            1,
        )

    include_signature = """app.include_router(
    wind_field_router
)"""

    if include_signature not in updated:
        root_marker = None

        for marker in (
            '@app.get("/")',
            "@app.get('/')",
        ):
            if marker in updated:
                root_marker = marker
                break

        if root_marker is None:
            raise RuntimeError(
                "backend/main.py root route marker not found"
            )

        updated = updated.replace(
            root_marker,
            INCLUDE_BLOCK
            + root_marker,
            1,
        )

    return updated


def main() -> int:
    required = [
        MAIN,
        REPO_ROOT
        / "backend"
        / "services"
        / "ecmwf_wind_forcing.py",
        REPO_ROOT
        / "backend"
        / "services"
        / "wind_field.py",
        REPO_ROOT
        / "backend"
        / "api"
        / "wind_field.py",
        REPO_ROOT
        / "tests"
        / "test_wind_field_service.py",
        REPO_ROOT
        / "tests"
        / "test_wind_field_api.py",
    ]

    for path in required:
        if not path.exists():
            print(
                f"ERROR: prerequisite/package file missing: {path}"
            )
            return 2

    original = MAIN.read_text(
        encoding="utf-8"
    )

    try:
        updated = patch_main(
            original
        )
    except RuntimeError as exc:
        print(
            f"ERROR: {exc}"
        )
        print(
            "backend/main.py was not modified."
        )
        return 3

    if updated == original:
        print(
            "WEATHER-1.5A wind-field API already installed."
        )
        return 0

    backup = backup_main()

    MAIN.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        "WEATHER-1.5A ECMWF Wind Field API v0.1 installed."
    )
    print("Added:")
    print("  backend/services/wind_field.py")
    print("  backend/api/wind_field.py")
    print("  tests/test_wind_field_service.py")
    print("  tests/test_wind_field_api.py")
    print("  tools/weather1_5a_wind_field_probe.py")
    print("Modified:")
    print("  backend/main.py")
    print("Endpoint:")
    print("  GET /weather/wind-field")
    print("Backup:")
    print(
        f"  {backup.relative_to(REPO_ROOT)}"
    )
    print(
        "No frontend, OceanDrift, or impact files were modified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
