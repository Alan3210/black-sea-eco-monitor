from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5c2_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/index.html": "1cafed36c2cc5ba42ef4fd7e53fed920c5304e7a2a1a3f5d2080a37a9a3135ff",
    "frontend/src/main.js": "a18155df8afb9a0fae5a08ceed5ccbcf43aad3b703e6ced67124358271201545",
    "frontend/src/i18n.js": "5670a30e3f552536372267364b7296457143e8883daedc45f63d522f1ed9248c",
    "frontend/src/windParticles.js": "58ee22d1a284a86dd9c2b35eef0f00edd29ab5451de1f3e253ff0b461c5b3c31",
    "frontend/src/windParticles.test.js": "8845a74672d944e04d1ba431d2f715f73345d9de5af24ede045db80df4371f2a",
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
            "dark navy halo"
            in text
            and "normalizeWindParticleSizePercent"
            in text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5C.2 wind particle contrast/size fix already installed."
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
                f".weather1_5c2_payload/{rel}"
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
            "ERROR: frontend files do not match the clean WEATHER-1.5C.1 baseline."
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
                f".before_weather1_5c2_"
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
        "WEATHER-1.5C.2 Wind Particle Contrast + Size v0.1 installed."
    )
    print(
        "Fixed:"
    )
    print(
        "  bright ice-cyan particle core + dark navy contrast halo"
    )
    print(
        "  dedicated particle-size slider (60%..200%)"
    )
    print(
        "Clarification:"
    )
    print(
        "  the existing 'Arrow size' slider remains disabled in particle-only mode by design."
    )
    print(
        "  the new 'Particle size' slider is active in Particles and Arrows + particles modes."
    )
    print(
        "No backend, ECMWF data, OpenDrift, windage, currents, or impact physics were modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
