from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5d5_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/index.html": "e104b86c847fc12d5d59841bf07e553b88ab6c6b3af2a1d71ca19680be80c75e",
    "frontend/src/i18n.js": "c1e7fb001e2765fb2a91efe4de1c1b8be91f17da7623643e715dfa2a94413489",
    "frontend/src/style.css": "d2fa0cdeb5619331e8cfdc239e60ef64f0b6ee25f4725bab46fc549220dd003f",
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
            '<h1 data-i18n="site.title">ЭКОМОНИТОР</h1>'
            in text
            and "monitor-status__visually-hidden"
            in text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5D.5 Header Cleanup + Status Dot v0.1 already installed."
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
                f".weather1_5d5_payload/{rel}"
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
            "ERROR: frontend does not match the clean WEATHER-1.5D.4 baseline."
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
                f".before_weather1_5d5_"
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
        "WEATHER-1.5D.5 Header Cleanup + Status Dot v0.1 installed."
    )
    print(
        "Changed:"
    )
    print(
        "  removed visible 'ECOLOGICAL ANALYTICS' eyebrow"
    )
    print(
        "  renamed product header to ECOMONITOR / ЭКОМОНИТОР"
    )
    print(
        "  removed visible monitoring/update text from the top bar"
    )
    print(
        "  kept the live connection-state dot as the rightmost indicator"
    )
    print(
        "  added a clear gap between the top bar and side panels"
    )
    print(
        "No JavaScript logic, backend APIs, ECMWF, Copernicus, OpenDrift, or model physics were modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
