from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5c_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/index.html": "56156ad918c004a85afae26dfb5fbe60630cfc21e55ccfc4c071ad3558943370",
    "frontend/src/main.js": "b28826115b5ac6ae55716e49dee4d1023770e552e6d7ac9dde590e78170055d8",
    "frontend/src/i18n.js": "95970cfc4baa7030395a3f579416d23e381ad6a651228752939502ec96c894c5",
    "frontend/src/style.css": "3aeabefdffb8d59d66be39561fa9e157206ca48f3b496d7515e777b9639bb121",
}

NEW_FILES = [
    "frontend/src/windParticles.js",
    "frontend/src/windParticles.test.js",
]


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
        / "main.js"
    )

    if (
        marker.exists()
        and "WEATHER-1.5C" in marker.read_text(
            encoding="utf-8",
            errors="replace",
        )
    ):
        cleanup_payload()
        print(
            "WEATHER-1.5C Web GIS wind particles already installed."
        )
        return 0

    missing = []

    for rel in TARGETS:
        path = REPO_ROOT / rel
        payload = PAYLOAD_ROOT / rel

        if not path.exists():
            missing.append(
                rel
            )

        if not payload.exists():
            missing.append(
                f".weather1_5c_payload/{rel}"
            )

    for rel in NEW_FILES:
        if not (
            REPO_ROOT / rel
        ).exists():
            missing.append(
                rel
            )

    if missing:
        print(
            "ERROR: package/repository files are missing:"
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
            "ERROR: frontend source does not match the clean WEATHER-1.5B baseline used to build WEATHER-1.5C."
        )
        print(
            "No tracked frontend files were modified."
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

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
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
                f".before_weather1_5c_"
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
        "WEATHER-1.5C Web GIS Wind Particles v0.1 installed."
    )
    print(
        "Modified:"
    )
    print(
        "  frontend/index.html"
    )
    print(
        "  frontend/src/main.js"
    )
    print(
        "  frontend/src/i18n.js"
    )
    print(
        "  frontend/src/style.css"
    )
    print(
        "Added:"
    )
    print(
        "  frontend/src/windParticles.js"
    )
    print(
        "  frontend/src/windParticles.test.js"
    )
    print(
        "Modes:"
    )
    print(
        "  arrows | particles | both"
    )
    print(
        "No backend, ECMWF API, Copernicus currents, OpenDrift, or impact physics were modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
