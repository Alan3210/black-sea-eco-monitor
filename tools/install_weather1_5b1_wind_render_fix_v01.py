from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = (
    REPO_ROOT
    / ".weather1_5b1_payload"
)
BACKUP_DIR = (
    REPO_ROOT
    / "dev-snapshots"
)

TARGETS = {
    "frontend/src/wind.js": "0fd0b9475fc632e375c50e977d4ca016c0d29f2a34e4632541f0ee7a87d8de91",
    "frontend/src/wind.test.js": "3b1eee7f56292b68bc9b421f98f8b628eadc85c0cbae5be27683204eb7821c69",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def cleanup_payload() -> None:
    if PAYLOAD_ROOT.exists():
        shutil.rmtree(
            PAYLOAD_ROOT,
        )


def main() -> int:
    marker = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "wind.js"
    )

    if marker.exists():
        text = marker.read_text(
            encoding="utf-8",
            errors="replace",
        )
        if (
            "normalizeWindFieldPayload idempotent"
            in text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5B.1 wind render fix already installed."
            )
            return 0

    missing = []

    for rel in TARGETS:
        if not (
            REPO_ROOT / rel
        ).exists():
            missing.append(rel)

        if not (
            PAYLOAD_ROOT / rel
        ).exists():
            missing.append(
                f".weather1_5b1_payload/{rel}"
            )

    if missing:
        print(
            "ERROR: required files are missing:"
        )
        for rel in missing:
            print(
                f"  {rel}"
            )
        return 2

    mismatches = []

    for rel, expected in TARGETS.items():
        actual = sha256(
            REPO_ROOT / rel
        )
        if actual != expected:
            mismatches.append(
                (
                    rel,
                    expected,
                    actual,
                )
            )

    if mismatches:
        print(
            "ERROR: current wind frontend files do not match the clean WEATHER-1.5B baseline."
        )
        print(
            "No tracked files were modified."
        )
        for (
            rel,
            expected,
            actual,
        ) in mismatches:
            print(
                f"  {rel}"
            )
            print(
                f"    expected: {expected}"
            )
            print(
                f"    actual:   {actual}"
            )
        return 3

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    backups = {}

    for rel in TARGETS:
        source = REPO_ROOT / rel
        safe_name = (
            rel
            .replace("/", "_")
            .replace("\\", "_")
        )
        backup = (
            BACKUP_DIR
            / (
                f"{safe_name}"
                f".before_weather1_5b1_"
                f"{stamp}"
            )
        )
        shutil.copy2(
            source,
            backup,
        )
        backups[rel] = backup

    try:
        for rel in TARGETS:
            shutil.copy2(
                PAYLOAD_ROOT / rel,
                REPO_ROOT / rel,
            )
    except Exception:
        for rel, backup in backups.items():
            shutil.copy2(
                backup,
                REPO_ROOT / rel,
            )
        raise

    cleanup_payload()

    print(
        "WEATHER-1.5B.1 Wind Render Fix v0.1 installed."
    )
    print(
        "Fixed:"
    )
    print(
        "  frontend/src/wind.js"
    )
    print(
        "  frontend/src/wind.test.js"
    )
    print(
        "Root cause:"
    )
    print(
        "  fetchWindField normalized API vectors once,"
    )
    print(
        "  then windToFeatureCollection normalized them again."
    )
    print(
        "  The second pass expected u_ms/v_ms/speed_ms,"
    )
    print(
        "  while the first pass had already renamed them to u/v/speed."
    )
    print(
        "  Result: 420 vectors in UI status, but 0 GeoJSON features on the map."
    )
    print(
        "No backend, MapLibre layer geometry, currents, drift, or impact physics were changed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
