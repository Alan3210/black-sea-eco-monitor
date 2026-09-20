from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (
    ROOT
    / "_air1_4c1_payload"
    / "frontend/src/tropomiOperationalField.test.js"
)
TARGET = ROOT / "frontend/src/tropomiOperationalField.test.js"


def main() -> int:
    if not PAYLOAD.exists():
        print("ERROR: AIR-1.4C.1 payload missing.")
        return 2

    if not TARGET.exists():
        print("ERROR: AIR-1.4C test file not found.")
        print("Install AIR-1.4C before AIR-1.4C.1.")
        return 3

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = (
        ROOT
        / "dev-snapshots"
        / f"air1_4c1_before_apply_{stamp}"
        / "frontend/src/tropomiOperationalField.test.js"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup)

    shutil.copy2(PAYLOAD, TARGET)

    verify = TARGET.read_text(encoding="utf-8")
    if "from 'vitest'" in verify:
        shutil.copy2(backup, TARGET)
        print("ERROR: vitest import still present; backup restored.")
        return 4

    if "from 'node:test'" not in verify:
        shutil.copy2(backup, TARGET)
        print("ERROR: node:test import missing; backup restored.")
        return 5

    shutil.rmtree(ROOT / "_air1_4c1_payload")

    print("AIR-1.4C.1 Node Test Compatibility Fix v0.1 installed.")
    print("Cause fixed: project test runner is node --test, not Vitest")
    print("Removed dependency on package: vitest")
    print("Test imports now use: node:test + node:assert/strict")
    print("Production TROPOMI runtime code: UNCHANGED")
    print("Modified:")
    print("  frontend\\src\\tropomiOperationalField.test.js")
    print("Backup:")
    print(backup.parent.parent.parent.parent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
