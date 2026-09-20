from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_5c_payload"

FILES = [
    (
        PAYLOAD / "backend/services/air_model_crosscheck.py",
        ROOT / "backend/services/air_model_crosscheck.py",
    ),
    (
        PAYLOAD / "backend/api/air_model_crosscheck.py",
        ROOT / "backend/api/air_model_crosscheck.py",
    ),
    (
        PAYLOAD / "tests/test_air_model_crosscheck.py",
        ROOT / "tests/test_air_model_crosscheck.py",
    ),
    (
        PAYLOAD / "tools/air1_5c_model_crosscheck_probe.py",
        ROOT / "tools/air1_5c_model_crosscheck_probe.py",
    ),
]

PREREQUISITES = [
    ROOT / "backend/services/cams_air_field.py",
    ROOT / "backend/services/geos_cf_field.py",
    ROOT / "backend/api/geos_cf_field.py",
]
MAIN = ROOT / "backend/main.py"

IMPORT_ANCHOR = (
    "from backend.api.geos_cf_field import router as geos_cf_field_router"
)
NEW_IMPORT = (
    "from backend.api.air_model_crosscheck import "
    "router as air_model_crosscheck_router"
)
ROUTER_ANCHOR = "app.include_router(geos_cf_field_router)"
NEW_ROUTER = "app.include_router(air_model_crosscheck_router)"


def backup(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    target = backup_root / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def patch_main(text: str) -> str:
    if NEW_IMPORT not in text:
        if IMPORT_ANCHOR not in text:
            raise RuntimeError(
                "backend/main.py GEOS-CF import anchor missing."
            )
        text = text.replace(
            IMPORT_ANCHOR,
            IMPORT_ANCHOR + "\n" + NEW_IMPORT,
            1,
        )

    if NEW_ROUTER not in text:
        if ROUTER_ANCHOR not in text:
            raise RuntimeError(
                "backend/main.py GEOS-CF router anchor missing."
            )
        text = text.replace(
            ROUTER_ANCHOR,
            ROUTER_ANCHOR + "\n" + NEW_ROUTER,
            1,
        )
    return text


def main() -> int:
    missing_prereq = [str(path) for path in PREREQUISITES if not path.exists()]
    if missing_prereq:
        print("ERROR: AIR-1.5C prerequisite missing:")
        for item in missing_prereq:
            print(f"  {item}")
        return 2

    missing_payload = [str(src) for src, _ in FILES if not src.exists()]
    if missing_payload:
        print("ERROR: AIR-1.5C payload incomplete:")
        for item in missing_payload:
            print(f"  {item}")
        return 3

    if not MAIN.exists():
        print("ERROR: backend/main.py not found.")
        return 4

    main_old = MAIN.read_text(encoding="utf-8")
    try:
        main_new = patch_main(main_old)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No files modified.")
        return 5

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_5c_before_apply_{stamp}"
    )

    backup(MAIN, backup_root)
    for _, dst in FILES:
        backup(dst, backup_root)

    installed = []
    for src, dst in FILES:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        installed.append(dst.relative_to(ROOT))

    MAIN.write_text(main_new, encoding="utf-8", newline="\n")

    verify = MAIN.read_text(encoding="utf-8")
    if NEW_IMPORT not in verify or NEW_ROUTER not in verify:
        print("ERROR: AIR-1.5C router registration verification failed.")
        return 6

    shutil.rmtree(PAYLOAD)

    print("AIR-1.5C CAMS/GEOS-CF Time-Aligned Cross-Check v0.1 installed.")
    print("REAL API: GET /air/model-crosscheck")
    print("Products: PM2.5 and PM10 only")
    print("Time alignment: GEOS valid time -> nearest CAMS whole hour")
    print("Default maximum time gap: 45 minutes")
    print("Spatial reference grid: GEOS-CF")
    print("CAMS resampling: bilinear to GEOS-CF cell centres")
    print("Invalid interpolation corners: comparison point skipped")
    print("Metrics: bias, MAE, median abs diff, RMSE, Pearson r, symmetric relative diff")
    print("Agreement thresholds: NOT calibrated / NOT applied")
    print("Neither model is treated as ground truth")
    print("Added:")
    for item in installed:
        print(f"  {item}")
    print("Modified:")
    print("  backend\\main.py")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
