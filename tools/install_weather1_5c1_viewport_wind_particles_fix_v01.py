from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5c1_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/src/windParticles.js": "3e979f3d99d77ca943d675b84b96e8c497cfc3597153bafc7f750a7d377c731e",
    "frontend/src/windParticles.test.js": "2bb9f166fac4ce11e05165a00638664fdbab32ac04ba314727e3ef1a147280e4",
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
        / "windParticles.js"
    )

    if marker.exists():
        text = marker.read_text(
            encoding="utf-8",
            errors="replace",
        )
        if (
            "particle population follow the currently visible viewport"
            in text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5C.1 viewport particle fix already installed."
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
                f".weather1_5c1_payload/{rel}"
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
            "ERROR: current wind-particle files do not match the clean WEATHER-1.5C v0.1 baseline."
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
                f".before_weather1_5c1_"
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
        "WEATHER-1.5C.1 Viewport Wind Particles Fix v0.1 installed."
    )
    print(
        "Fixed:"
    )
    print(
        "  frontend/src/windParticles.js"
    )
    print(
        "  frontend/src/windParticles.test.js"
    )
    print(
        "Root cause:"
    )
    print(
        "  particles were seeded across the entire Black Sea field."
    )
    print(
        "  At regional zoom only a tiny fraction landed inside the viewport."
    )
    print(
        "  Diagnostics confirmed the canvas was visible and drawing,"
    )
    print(
        "  but only a handful of high-alpha pixels were on screen."
    )
    print(
        "Fix:"
    )
    print(
        "  particle spawning is now viewport-aware and reseeds after map movement."
    )
    print(
        "  particle strokes are also slightly more legible."
    )
    print(
        "No backend, ECMWF data, OpenDrift, windage, currents, or impact physics were modified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
