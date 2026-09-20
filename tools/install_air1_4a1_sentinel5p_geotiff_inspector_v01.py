from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_4a1_payload"

FILES = [
    (
        PAYLOAD / "tools/air1_4a1_sentinel5p_inspector.py",
        ROOT / "tools/air1_4a1_sentinel5p_inspector.py",
    ),
    (
        PAYLOAD / "tests/test_air1_4a1_sentinel5p_inspector.py",
        ROOT / "tests/test_air1_4a1_sentinel5p_inspector.py",
    ),
]


def main() -> int:
    missing = [str(src) for src, _ in FILES if not src.exists()]
    if missing:
        print("ERROR: AIR-1.4A.1 payload incomplete:")
        for item in missing:
            print(f"  {item}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_4a1_before_apply_{stamp}"
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

    print("AIR-1.4A.1 Sentinel-5P GeoTIFF Inspector v0.1 installed.")
    print("Purpose: inspect REAL cached TROPOMI raster before API normalization")
    print("Checks: CRS, bounds, transform, dtype, bands, dataMask, valid coverage")
    print("Stats: min/max/mean + P05/P25/P50/P75/P95")
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
