from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5c3_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/src/windParticles.js": "a735c94da4e7648bd98d9c2e149005770eabdab086d04a89f1c23eb4fae53b96",
    "frontend/src/windParticles.test.js": "716a63c3627659794975c48a8e3569eb106125b2d99d66083958f1b2d1366cbc",
}


def normalized_sha256(path: Path) -> str:
    text = path.read_text(
        encoding="utf-8",
    ).replace(
        "\r\n",
        "\n",
    )

    return hashlib.sha256(
        text.encode(
            "utf-8",
        )
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
        / "windParticles.js"
    )

    if marker.exists():
        text = marker.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if (
            "Bilinear interpolation keeps u and v continuous"
            in text
            and "sampleWindVectorInverseDistance"
            in text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5C.3 smooth wind particle interpolation already installed."
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
                f".weather1_5c3_payload/{rel}"
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
        actual = normalized_sha256(
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
            "ERROR: frontend files do not match the clean WEATHER-1.5C.2 baseline."
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
                f".before_weather1_5c3_"
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
        "WEATHER-1.5C.3 Smooth Wind Particle Interpolation v0.1 installed."
    )
    print(
        "Fixed:"
    )
    print(
        "  regular ECMWF wind grid -> bilinear u/v interpolation for particle advection"
    )
    print(
        "  incomplete-grid fallback -> smooth inverse-distance interpolation"
    )
    print(
        "  removes nearest-neighbour cell seams from accumulated particle trails"
    )
    print(
        "Unchanged:"
    )
    print(
        "  backend /weather/wind-field, ECMWF data, stride, OpenDrift, windage, currents and impact physics"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
