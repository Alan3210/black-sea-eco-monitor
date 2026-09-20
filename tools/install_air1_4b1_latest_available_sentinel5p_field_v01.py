from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_4b1_payload"

FILES = [
    (
        PAYLOAD / "backend/services/sentinel5p_satellite_field.py",
        ROOT / "backend/services/sentinel5p_satellite_field.py",
    ),
    (
        PAYLOAD / "backend/api/satellite_air_field.py",
        ROOT / "backend/api/satellite_air_field.py",
    ),
    (
        PAYLOAD / "tests/test_sentinel5p_satellite_field.py",
        ROOT / "tests/test_sentinel5p_satellite_field.py",
    ),
    (
        PAYLOAD / "tools/air1_4b_satellite_field_probe.py",
        ROOT / "tools/air1_4b_satellite_field_probe.py",
    ),
]

PREREQUISITES = [
    ROOT / "backend/services/sentinel5p_provider.py",
    ROOT / "backend/services/sentinel5p_satellite_field.py",
    ROOT / "backend/api/satellite_air_field.py",
]


def main() -> int:
    missing_prereq = [str(p) for p in PREREQUISITES if not p.exists()]
    if missing_prereq:
        print("ERROR: AIR-1.4B prerequisite missing:")
        for item in missing_prereq:
            print(f"  {item}")
        print("Install AIR-1.4A and AIR-1.4B before AIR-1.4B.1.")
        return 2

    missing_payload = [str(src) for src, _ in FILES if not src.exists()]
    if missing_payload:
        print("ERROR: AIR-1.4B.1 payload incomplete:")
        for item in missing_payload:
            print(f"  {item}")
        return 3

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_4b1_before_apply_{stamp}"
    )

    changed = []
    for src, dst in FILES:
        if dst.exists():
            backup = backup_root / dst.relative_to(ROOT)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, backup)

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        changed.append(dst.relative_to(ROOT))

    shutil.rmtree(PAYLOAD)

    print("AIR-1.4B.1 Latest Available Sentinel-5P Field v0.1 installed.")
    print("Default /air/satellite-field behavior: latest valid coverage")
    print("Explicit ?date=YYYY-MM-DD behavior: exact day only")
    print("Default lookback: 7 days; API range: 0..14")
    print("Empty current day is skipped, not reported as latest data")
    print("Response selection metadata: mode/resolved_date/lookback/candidates")
    print("No interpolation added; scientific semantics unchanged")
    print("Modified:")
    for item in changed:
        print(f"  {item}")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
