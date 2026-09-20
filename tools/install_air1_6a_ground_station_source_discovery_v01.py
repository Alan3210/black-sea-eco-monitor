from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_6a_payload"

FILES = [
    (
        PAYLOAD / "backend/services/ground_station_source_registry.py",
        ROOT / "backend/services/ground_station_source_registry.py",
    ),
    (
        PAYLOAD / "tests/test_ground_station_source_discovery.py",
        ROOT / "tests/test_ground_station_source_discovery.py",
    ),
    (
        PAYLOAD / "tools/air1_6a_ground_station_source_probe.py",
        ROOT / "tools/air1_6a_ground_station_source_probe.py",
    ),
]


def main() -> int:
    missing = [str(src) for src, _ in FILES if not src.exists()]
    if missing:
        print("ERROR: AIR-1.6A payload incomplete:")
        for item in missing:
            print(f"  {item}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_6a_before_apply_{stamp}"
    )

    installed = []
    for src, dst in FILES:
        if dst.exists():
            backup = backup_root / dst.relative_to(ROOT)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, backup)

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        installed.append(dst.relative_to(ROOT))

    shutil.rmtree(PAYLOAD)

    print("AIR-1.6A Ground Station Source Discovery v0.1 installed.")
    print("Production decision:")
    print("  EEA E2a API -> PRIMARY machine source for BG + RO")
    print("  Türkiye official portal -> local provider track")
    print("  Georgia official portal -> local provider track")
    print("  Ukraine official open data -> secondary/local provider track")
    print("  Russia -> local source track; no stable public API validated yet")
    print("  OpenAQ -> remains excluded")
    print("Semantics:")
    print("  EEA E2a = station_measurement + up-to-date/unverified")
    print("No Web GIS or production station API is added in AIR-1.6A.")
    print("Added:")
    for item in installed:
        print(f"  {item}")
    if backup_root.exists():
        print("Backup:")
        print(backup_root)
    else:
        print("Backup: not needed (new files only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
