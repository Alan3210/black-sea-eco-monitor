from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5d3_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/index.html": "2e5fa3ef577884aaf5128800fb1304189aa1ac2ee7eb18744a7e083de98c10bb",
    "frontend/src/i18n.js": "50c941990afbd89ee9a29afb00e71bc96524e7bfd24b8944c3e637d5ce80e509",
    "frontend/src/style.css": "768291726263ba9a2c0aa509721eb97925ba8eea970463e37ebfd8d0951bc171",
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
    marker = REPO_ROOT / "frontend/src/i18n.js"

    if marker.exists():
        text = marker.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if (
            "Ветер · высота 10 м"
            in text
            and "10 м — высота над поверхностью, не скорость ветра."
            in text
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5D.3 Header Readability + Wind Height v0.1 already installed."
            )
            return 0

    missing = []

    for rel in TARGETS:
        if not (REPO_ROOT / rel).exists():
            missing.append(rel)

        if not (PAYLOAD_ROOT / rel).exists():
            missing.append(
                f".weather1_5d3_payload/{rel}"
            )

    if missing:
        print("ERROR: required files are missing:")
        for rel in missing:
            print(f"  {rel}")
        return 2

    mismatches = []

    for rel, expected in TARGETS.items():
        actual = sha256(REPO_ROOT / rel)
        if actual != expected:
            mismatches.append(
                (rel, expected, actual)
            )

    if mismatches:
        print(
            "ERROR: frontend does not match the clean WEATHER-1.5D.2 baseline."
        )
        print(
            "No tracked files were modified."
        )

        for rel, expected, actual in mismatches:
            print(f"  {rel}")
            print(f"    expected: {expected}")
            print(f"    actual:   {actual}")

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
        safe = (
            rel
            .replace("/", "_")
            .replace("\\", "_")
        )
        backup = (
            BACKUP_DIR
            / f"{safe}.before_weather1_5d3_{stamp}"
        )

        shutil.copy2(source, backup)
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
        "WEATHER-1.5D.3 Header Readability + Wind Height v0.1 installed."
    )
    print("Changed:")
    print(
        "  larger operational header typography and wider field cards"
    )
    print(
        "  '10 m' clarified as wind measurement height above the surface"
    )
    print(
        "  sidebar note explicitly states that 10 m is not wind speed"
    )
    print(
        "No JavaScript logic, backend APIs, ECMWF, Copernicus, OpenDrift, or model physics were modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
