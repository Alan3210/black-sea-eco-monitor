from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "backend" / "main.py"

IMPORT_LINE = (
    "from backend.api.impact import router as impact_router"
)

INCLUDE_BLOCK = """


app.include_router(
    impact_router
)
"""


def patched_text(original: str) -> str:
    text = original

    if IMPORT_LINE not in text:
        marker = "from fastapi import FastAPI"

        if marker not in text:
            raise RuntimeError(
                "Could not find FastAPI import in backend/main.py"
            )

        text = text.replace(
            marker,
            marker + "\n\n" + IMPORT_LINE,
            1,
        )

    if "app.include_router(\n    impact_router\n)" not in text:
        marker = '@app.get("/")'

        if marker not in text:
            raise RuntimeError(
                "Could not find root endpoint marker in backend/main.py"
            )

        text = text.replace(
            marker,
            INCLUDE_BLOCK + "\n" + marker,
            1,
        )

    return text


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the patch. Without this flag, only validate.",
    )

    args = parser.parse_args()

    if not MAIN_PATH.exists():
        print(
            f"ERROR: {MAIN_PATH} does not exist."
        )
        return 1

    original = MAIN_PATH.read_text(
        encoding="utf-8-sig"
    )

    try:
        updated = patched_text(
            original
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    if updated == original:
        print(
            "backend/main.py already contains Impact Forecast v0.1 router."
        )
        return 0

    if not args.apply:
        print("DRY RUN")
        print(
            "backend/main.py can be patched safely."
        )
        print("No files changed.")
        return 0

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup = MAIN_PATH.with_name(
        f"main.before_impact_v01_{stamp}.py"
    )

    shutil.copy2(
        MAIN_PATH,
        backup,
    )

    MAIN_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        "Impact Forecast v0.1 router installed."
    )
    print(
        f"Backup: {backup}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
