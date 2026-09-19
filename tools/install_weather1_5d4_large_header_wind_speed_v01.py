from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5d4_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/index.html": "4e938f716b46b7e2cd28394fc8d8dc841ee4cbbf2133404aacab860c497a38d2",
    "frontend/src/i18n.js": "097e98a1adb5b4217b6b387471922c51141b00abfaf23bdb731fcc5b8afc8150",
    "frontend/src/style.css": "00a180cd1a4981ca2cf7267ee77973975244b0cb94163d58d3cba1be8762ebaa",
    "frontend/src/main.js": "607804925622cab18d54a62d7426182694c903d51081dae4d283815bbaf83d13",
    "frontend/src/combinedFields.js": "bf54029a93e89dba4ca2803ec779d39d93e8703d00a02d9df5c5b3ca8b8989ce",
    "frontend/src/combinedFields.test.js": "97448bf382d8d135c3ce27e77b525ec2fdc8bb7999485fdc5750a3ff4188fadf",
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
        / "index.html"
    )

    if marker.exists():
        text = marker.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if (
            'id="combined-wind-speed"'
            in text
            and "Ветер · высота 10 м"
            not in text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5D.4 Large Header + Wind Speed v0.1 already installed."
            )
            return 0

    missing = []

    for rel in TARGETS:
        if not (
            REPO_ROOT / rel
        ).exists():
            missing.append(
                rel
            )

        if not (
            PAYLOAD_ROOT / rel
        ).exists():
            missing.append(
                f".weather1_5d4_payload/{rel}"
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
            "ERROR: frontend does not match the clean WEATHER-1.5D.3 baseline."
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
                f".before_weather1_5d4_"
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
        "WEATHER-1.5D.4 Large Header + Wind Speed v0.1 installed."
    )
    print(
        "Changed:"
    )
    print(
        "  fixed top bar enlarged for operational readability"
    )
    print(
        "  wind header now shows field-wide MEAN speed in m/s"
    )
    print(
        "  operator-facing wind height label removed"
    )
    print(
        "  exact local wind speed remains available on wind-vector click"
    )
    print(
        "  filter/event panels moved down to clear the taller top bar"
    )
    print(
        "No backend APIs, ECMWF wind values, Copernicus currents, OpenDrift, windage, or impact physics were modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
