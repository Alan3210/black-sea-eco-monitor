from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "frontend/index.html"

TROPOMI_BLOCK = '<div id="tropomi-air-root" class="tropomi-air-root"></div>'
DRIFT_ANCHOR = '<div class="drift-control">'


def main() -> int:
    if not INDEX.exists():
        print("ERROR: frontend/index.html not found.")
        return 2

    text = INDEX.read_text(encoding="utf-8")

    tropomi_count = text.count(TROPOMI_BLOCK)
    drift_count = text.count(DRIFT_ANCHOR)

    if tropomi_count != 1:
        print(
            f"ERROR: expected exactly one TROPOMI root, found {tropomi_count}."
        )
        print("No files modified.")
        return 3

    if drift_count != 1:
        print(
            f"ERROR: expected exactly one drift-control anchor, found {drift_count}."
        )
        print("No files modified.")
        return 4

    # Remove the misplaced root first.
    without_tropomi = text.replace(TROPOMI_BLOCK, "", 1)

    drift_pos = without_tropomi.find(DRIFT_ANCHOR)
    line_start = without_tropomi.rfind("\n", 0, drift_pos) + 1
    indent = without_tropomi[line_start:drift_pos]

    insertion = (
        f'{indent}<div id="tropomi-air-root" '
        f'class="tropomi-air-root"></div>\n\n'
    )

    updated = (
        without_tropomi[:line_start]
        + insertion
        + without_tropomi[line_start:]
    )

    # Verify exact ordering: CAMS content must be before TROPOMI,
    # and TROPOMI must be immediately before Drift.
    cams_pos = updated.find('id="cams-air-panel"')
    tropomi_pos = updated.find('id="tropomi-air-root"')
    drift_pos = updated.find(DRIFT_ANCHOR)

    if not (cams_pos >= 0 and cams_pos < tropomi_pos < drift_pos):
        print("ERROR: placement verification failed.")
        print("No files modified.")
        return 5

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = (
        ROOT
        / "dev-snapshots"
        / f"air1_4c3_before_apply_{stamp}"
        / "frontend/index.html"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INDEX, backup)

    INDEX.write_text(updated, encoding="utf-8", newline="\n")

    verify = INDEX.read_text(encoding="utf-8")
    verify_cams = verify.find('id="cams-air-panel"')
    verify_tropomi = verify.find('id="tropomi-air-root"')
    verify_drift = verify.find(DRIFT_ANCHOR)

    if not (
        verify.count(TROPOMI_BLOCK) == 1
        and verify_cams < verify_tropomi < verify_drift
    ):
        shutil.copy2(backup, INDEX)
        print("ERROR: post-write verification failed; backup restored.")
        return 6

    print("AIR-1.4C.3 TROPOMI Placement Fix v0.1 installed.")
    print("TROPOMI root moved from page-bottom placement to Atmosphere section.")
    print("New order:")
    print("  CAMS")
    print("  TROPOMI")
    print("  Drift Forecast")
    print("No JS/CSS/runtime logic changed.")
    print("Modified:")
    print("  frontend\\index.html")
    print("Backup:")
    print(backup.parent.parent.parent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
