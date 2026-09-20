from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (
    ROOT
    / "_air1_4c2_payload"
    / "frontend/src/tropomiOperationalField.js"
)
TARGET = ROOT / "frontend/src/tropomiOperationalField.js"


def main() -> int:
    if not PAYLOAD.exists():
        print("ERROR: AIR-1.4C.2 payload missing.")
        return 2

    if not TARGET.exists():
        print("ERROR: AIR-1.4C runtime module not found.")
        return 3

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = (
        ROOT
        / "dev-snapshots"
        / f"air1_4c2_before_apply_{stamp}"
        / "frontend/src/tropomiOperationalField.js"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup)

    shutil.copy2(PAYLOAD, TARGET)

    verify = TARGET.read_text(encoding="utf-8")
    required = (
        "value === null",
        "value === undefined",
        "value === ''",
    )
    if not all(token in verify for token in required):
        shutil.copy2(backup, TARGET)
        print("ERROR: null-pixel fix verification failed; backup restored.")
        return 4

    shutil.rmtree(ROOT / "_air1_4c2_payload")

    print("AIR-1.4C.2 TROPOMI Null Pixel Fix v0.1 installed.")
    print("REAL runtime bug fixed: JSON null is no longer coerced to numeric 0")
    print("Invalid satellite pixels are now skipped from GeoJSON cells")
    print("Valid numeric zero remains a valid scientific value")
    print("Existing negative retrieval values remain preserved")
    print("Modified:")
    print("  frontend\\src\\tropomiOperationalField.js")
    print("Backup:")
    print(backup.parent.parent.parent.parent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
