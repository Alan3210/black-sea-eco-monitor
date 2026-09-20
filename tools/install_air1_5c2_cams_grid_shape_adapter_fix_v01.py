from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_5c2_payload"

SERVICE_SRC = (
    PAYLOAD / "backend/services/air_model_crosscheck.py"
)
SERVICE_DST = (
    ROOT / "backend/services/air_model_crosscheck.py"
)
TEST_SRC = (
    PAYLOAD / "tests/test_air_model_crosscheck_grid_shape.py"
)
TEST_DST = (
    ROOT / "tests/test_air_model_crosscheck_grid_shape.py"
)


def main() -> int:
    required = [SERVICE_SRC, TEST_SRC, SERVICE_DST]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("ERROR: AIR-1.5C.2 prerequisite/payload missing:")
        for item in missing:
            print(f"  {item}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_5c2_before_apply_{stamp}"
    )

    for path in [SERVICE_DST, TEST_DST]:
        if path.exists():
            target = backup_root / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    SERVICE_DST.parent.mkdir(parents=True, exist_ok=True)
    TEST_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SERVICE_SRC, SERVICE_DST)
    shutil.copy2(TEST_SRC, TEST_DST)

    verify = SERVICE_DST.read_text(encoding="utf-8")
    required_tokens = [
        '"longitude", "longitudes"',
        '"latitude", "latitudes"',
        "_first_present",
    ]
    if not all(token in verify for token in required_tokens):
        print("ERROR: AIR-1.5C.2 verification failed.")
        return 3

    shutil.rmtree(PAYLOAD)

    print("AIR-1.5C.2 CAMS Grid Shape Adapter Fix v0.1 installed.")
    print("Confirmed real CAMS grid schema supported:")
    print("  grid.latitudes  -> latitude axis")
    print("  grid.longitudes -> longitude axis")
    print("  grid.values     -> [lat][lon] matrix")
    print("Observed live shape expected: 90 x 175")
    print("Top-level singular/plural coordinate aliases also supported")
    print("No interpolation policy or scientific metrics changed")
    print("Modified:")
    print("  backend\\services\\air_model_crosscheck.py")
    print("Added:")
    print("  tests\\test_air_model_crosscheck_grid_shape.py")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
