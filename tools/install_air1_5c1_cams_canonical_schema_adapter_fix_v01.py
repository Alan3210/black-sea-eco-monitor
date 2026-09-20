from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_5c1_payload"

SERVICE_SRC = (
    PAYLOAD / "backend/services/air_model_crosscheck.py"
)
SERVICE_DST = (
    ROOT / "backend/services/air_model_crosscheck.py"
)
TEST_SRC = (
    PAYLOAD / "tests/test_air_model_crosscheck_schema.py"
)
TEST_DST = (
    ROOT / "tests/test_air_model_crosscheck_schema.py"
)


def main() -> int:
    required = [SERVICE_SRC, TEST_SRC, SERVICE_DST]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("ERROR: AIR-1.5C.1 prerequisite/payload missing:")
        for item in missing:
            print(f"  {item}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_5c1_before_apply_{stamp}"
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
        "field.get(\"pollutant\")",
        "grid.get(\"longitude\")",
        "grid.get(\"latitude\")",
        "grid.get(\"values\")",
        "_normalize_unit_text",
    ]
    if not all(token in verify for token in required_tokens):
        print("ERROR: AIR-1.5C.1 verification failed.")
        return 3

    shutil.rmtree(PAYLOAD)

    print("AIR-1.5C.1 CAMS Canonical Schema Adapter Fix v0.1 installed.")
    print("Fixes real CAMS schema:")
    print("  units -> pollutant.units")
    print("  source_variable -> pollutant.source_variable")
    print("  longitude/latitude/values -> grid.* when nested")
    print("Unit normalization: µg/m3 == µg/m³ == ug/m3")
    print("No scientific values are converted or rescaled")
    print("Cross-check API contract unchanged")
    print("Modified:")
    print("  backend\\services\\air_model_crosscheck.py")
    print("Added:")
    print("  tests\\test_air_model_crosscheck_schema.py")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
