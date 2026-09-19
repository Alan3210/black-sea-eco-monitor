from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5d_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

BASELINE = {
    "frontend/index.html": "ab39cf58960651204488a1951319cf4c9bfb8b04c8dcf3815caae9020c1b4c2e",
    "frontend/src/main.js": "c7dfae0e20d04aae8f168a1fe9c9ee2e4bf3f7ac1b6789b78b143889db592a93",
    "frontend/src/i18n.js": "a40abfa035a9f1ca0cb6dec165ff51441de50a90a5065d348201eab24b0ebfc1",
    "frontend/src/style.css": "ea222cd3999303912c61d6cdb7520ed132fdeef31ff5383bc7ca348b7c662d2a",
}

MODIFIED = [
    "frontend/index.html",
    "frontend/src/main.js",
    "frontend/src/i18n.js",
    "frontend/src/style.css"
]
ADDED = [
    "frontend/src/combinedFields.js",
    "frontend/src/combinedFields.test.js"
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
        / "combinedFields.js"
    )

    if marker.exists():
        marker_text = marker.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if (
            "combinedFieldsViewModel"
            in marker_text
            and "combinedFieldTimeDeltaMinutes"
            in marker_text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5D Combined Operational Fields v0.1 already installed."
            )
            return 0

    missing = []

    for rel in MODIFIED + ADDED:
        if not (
            PAYLOAD_ROOT / rel
        ).exists():
            missing.append(
                f".weather1_5d_payload/{rel}"
            )

    for rel in MODIFIED:
        if not (
            REPO_ROOT / rel
        ).exists():
            missing.append(
                rel
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

    for rel, expected in BASELINE.items():
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
            "ERROR: frontend does not match the clean WEATHER-1.5C.3 baseline."
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

    collisions = [
        rel
        for rel in ADDED
        if (
            REPO_ROOT / rel
        ).exists()
    ]

    if collisions:
        print(
            "ERROR: WEATHER-1.5D new files already exist:"
        )

        for rel in collisions:
            print(
                f"  {rel}"
            )

        print(
            "No tracked files were modified."
        )
        return 4

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backups = {}

    for rel in MODIFIED:
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
                f".before_weather1_5d_"
                f"{stamp}"
            )
        )

        shutil.copy2(
            source,
            backup,
        )
        backups[rel] = backup

    created = []

    try:
        for rel in MODIFIED:
            shutil.copy2(
                PAYLOAD_ROOT / rel,
                REPO_ROOT / rel,
            )

        for rel in ADDED:
            destination = REPO_ROOT / rel
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            shutil.copy2(
                PAYLOAD_ROOT / rel,
                destination,
            )
            created.append(
                destination
            )
    except Exception:
        for rel, backup in backups.items():
            shutil.copy2(
                backup,
                REPO_ROOT / rel,
            )

        for destination in created:
            if destination.exists():
                destination.unlink()

        raise

    cleanup_payload()

    print(
        "WEATHER-1.5D Combined Operational Fields v0.1 installed."
    )
    print(
        "Added:"
    )
    print(
        "  top-center combined wind/current operational HUD"
    )
    print(
        "  separate Copernicus-current and ECMWF-wind identities"
    )
    print(
        "  each field valid time and active display mode"
    )
    print(
        "  absolute valid-time delta (Delta t)"
    )
    print(
        "  explicit independent-fields / not-resultant-vector semantics"
    )
    print(
        "No backend, ECMWF, Copernicus, OpenDrift, windage, or impact physics were modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
