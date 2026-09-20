from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_4a_payload"

FILES = [
    (
        PAYLOAD / "backend/services/sentinel5p_provider.py",
        ROOT / "backend/services/sentinel5p_provider.py",
    ),
    (
        PAYLOAD / "tests/test_sentinel5p_provider.py",
        ROOT / "tests/test_sentinel5p_provider.py",
    ),
    (
        PAYLOAD / "tools/air1_4a_sentinel5p_probe.py",
        ROOT / "tools/air1_4a_sentinel5p_probe.py",
    ),
]


def main() -> int:
    missing = [str(src) for src, _ in FILES if not src.exists()]
    if missing:
        print("ERROR: AIR-1.4A payload is incomplete:")
        for item in missing:
            print(f"  {item}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT
        / "dev-snapshots"
        / f"air1_4a_before_apply_{stamp}"
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

    # Remove temporary payload after successful install so it does not remain
    # as an untracked repository artifact.
    shutil.rmtree(PAYLOAD)

    print("AIR-1.4A Sentinel-5P/TROPOMI Provider v0.1 installed.")
    print("REAL production addition: Sentinel-5P L2 Process API provider")
    print("Source: Copernicus Data Space Ecosystem / Sentinel Hub")
    print("Output: cached FLOAT32 GeoTIFF + provenance metadata")
    print("Default Black Sea bbox: [26.0, 39.0, 43.5, 48.0]")
    print("NO2 QA threshold: 75%; other products: 50%")
    print("Resampling: NEAREST")
    print("Semantics: satellite column/aerosol observation, NOT surface concentration")
    print("Added:")
    for item in changed:
        print(f"  {item}")
    if backup_root.exists():
        print("Backup:")
        print(backup_root)
    else:
        print("Backup: not needed (new files only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
