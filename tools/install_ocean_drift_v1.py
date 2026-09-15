from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = REPO_ROOT / "backend" / "main.py"

IMPORT_LINE = (
    "from backend.api.ocean_drift "
    "import router as ocean_drift_router"
)

INCLUDE_BLOCK = (
    "\n\napp.include_router(\n"
    "    ocean_drift_router\n"
    ")\n"
)


def patch_main(text: str) -> str:
    updated = text

    if IMPORT_LINE not in updated:
        fastapi_import = (
            "from fastapi import FastAPI"
        )

        if fastapi_import not in updated:
            raise RuntimeError(
                "Could not find the FastAPI import "
                "in backend/main.py."
            )

        updated = updated.replace(
            fastapi_import,
            fastapi_import
            + "\n\n"
            + IMPORT_LINE,
            1,
        )

    include_marker = (
        "app.include_router(\n"
        "    ocean_drift_router\n"
        ")"
    )

    if include_marker not in updated:
        root_marker = '@app.get("/")'

        if root_marker not in updated:
            raise RuntimeError(
                'Could not find @app.get("/") '
                "in backend/main.py."
            )

        updated = updated.replace(
            root_marker,
            INCLUDE_BLOCK
            + "\n"
            + root_marker,
            1,
        )

    return updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
    )
    args = parser.parse_args()

    if not MAIN_PATH.exists():
        raise SystemExit(
            f"File not found: {MAIN_PATH}"
        )

    original = MAIN_PATH.read_text(
        encoding="utf-8"
    )
    patched = patch_main(
        original
    )

    if patched == original:
        print(
            "Ocean drift router is already installed."
        )
        return

    if not args.apply:
        print("DRY RUN")
        print(
            "backend/main.py can be patched safely."
        )
        print("No files changed.")
        print()
        print("Run:")
        print(
            "python tools/install_ocean_drift_v1.py --apply"
        )
        return

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup = MAIN_PATH.with_name(
        "main.before_ocean_drift_v1_"
        + stamp
        + ".py"
    )

    shutil.copy2(
        MAIN_PATH,
        backup,
    )

    MAIN_PATH.write_text(
        patched,
        encoding="utf-8",
    )

    print(f"Backup: {backup}")
    print("Patched backend/main.py")
    print("SUCCESS")


if __name__ == "__main__":
    main()
