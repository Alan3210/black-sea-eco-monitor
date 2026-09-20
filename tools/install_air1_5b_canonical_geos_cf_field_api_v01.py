from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_5b_payload"

FILES = [
    (
        PAYLOAD / "backend/services/geos_cf_field.py",
        ROOT / "backend/services/geos_cf_field.py",
    ),
    (
        PAYLOAD / "backend/api/geos_cf_field.py",
        ROOT / "backend/api/geos_cf_field.py",
    ),
    (
        PAYLOAD / "tests/test_geos_cf_field.py",
        ROOT / "tests/test_geos_cf_field.py",
    ),
    (
        PAYLOAD / "tools/air1_5b_geos_cf_field_probe.py",
        ROOT / "tools/air1_5b_geos_cf_field_probe.py",
    ),
]

PROVIDER = ROOT / "backend/services/geos_cf_provider.py"
MAIN = ROOT / "backend/main.py"

IMPORT_ANCHOR = (
    "from backend.api.air_field import router as air_field_router"
)
NEW_IMPORT = (
    "from backend.api.geos_cf_field import router as geos_cf_field_router"
)
ROUTER_ANCHOR = "app.include_router(air_field_router)"
NEW_ROUTER = "app.include_router(geos_cf_field_router)"


def backup(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    target = backup_root / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def patch_main(text: str) -> str:
    if NEW_IMPORT not in text:
        if IMPORT_ANCHOR not in text:
            raise RuntimeError("backend/main.py air_field import anchor missing.")
        text = text.replace(
            IMPORT_ANCHOR,
            IMPORT_ANCHOR + "\n" + NEW_IMPORT,
            1,
        )

    if NEW_ROUTER not in text:
        if ROUTER_ANCHOR not in text:
            raise RuntimeError(
                "backend/main.py air_field include_router anchor missing."
            )
        text = text.replace(
            ROUTER_ANCHOR,
            ROUTER_ANCHOR + "\n" + NEW_ROUTER,
            1,
        )

    return text


def main() -> int:
    if not PROVIDER.exists():
        print("ERROR: AIR-1.5A GEOS-CF provider prerequisite missing.")
        return 2

    missing = [str(src) for src, _ in FILES if not src.exists()]
    if missing:
        print("ERROR: AIR-1.5B payload incomplete:")
        for item in missing:
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
        ROOT / "dev-snapshots" / f"air1_5b_before_apply_{stamp}"
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
        print("ERROR: GEOS-CF router registration verification failed.")
        return 6

    shutil.rmtree(PAYLOAD)

    print("AIR-1.5B Canonical GEOS-CF Field API v0.1 installed.")
    print("REAL API: GET /air/geos-cf-field")
    print("Adds descriptive run/valid-time freshness metadata")
    print("Adds CAMS comparison-readiness metadata")
    print("PM2.5/PM10: unit compatible, but NOT direct-compare ready yet")
    print("Gas products: explicit unit conversion required")
    print("No model equivalence is assumed")
    print("Windows probe output: ASCII-safe JSON")
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
