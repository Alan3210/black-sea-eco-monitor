from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_4b_payload"

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

PROVIDER = ROOT / "backend/services/sentinel5p_provider.py"
MAIN = ROOT / "backend/main.py"
REQ = ROOT / "backend/requirements-air.txt"

IMPORT_ANCHOR = (
    "from backend.api.air_field import router as air_field_router"
)
NEW_IMPORT = (
    "from backend.api.satellite_air_field import "
    "router as satellite_air_field_router"
)
ROUTER_ANCHOR = "app.include_router(air_field_router)"
NEW_ROUTER = "app.include_router(satellite_air_field_router)"
RASTERIO_REQ = "rasterio>=1.5.1,<2"


def backup_file(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    target = backup_root / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def patch_main(text: str) -> str:
    if NEW_IMPORT not in text:
        if IMPORT_ANCHOR not in text:
            raise RuntimeError("backend/main.py import anchor not found.")
        text = text.replace(
            IMPORT_ANCHOR,
            IMPORT_ANCHOR + "\n" + NEW_IMPORT,
            1,
        )

    if NEW_ROUTER not in text:
        if ROUTER_ANCHOR not in text:
            raise RuntimeError(
                "backend/main.py include_router anchor not found."
            )
        text = text.replace(
            ROUTER_ANCHOR,
            ROUTER_ANCHOR + "\n" + NEW_ROUTER,
            1,
        )
    return text


def patch_requirements(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    if not any(
        line.strip().lower().startswith("rasterio")
        for line in lines
    ):
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(RASTERIO_REQ)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if not PROVIDER.exists():
        print("ERROR: AIR-1.4A prerequisite missing:")
        print("  backend\\services\\sentinel5p_provider.py")
        print("Install AIR-1.4A before AIR-1.4B.")
        return 2

    missing = [str(src) for src, _ in FILES if not src.exists()]
    if missing:
        print("ERROR: AIR-1.4B payload incomplete:")
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

    req_old = REQ.read_text(encoding="utf-8") if REQ.exists() else ""
    req_new = patch_requirements(req_old)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_4b_before_apply_{stamp}"
    )

    backup_file(MAIN, backup_root)
    backup_file(REQ, backup_root)
    for _, dst in FILES:
        backup_file(dst, backup_root)

    installed = []
    for src, dst in FILES:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        installed.append(dst.relative_to(ROOT))

    MAIN.write_text(main_new, encoding="utf-8", newline="\n")
    REQ.parent.mkdir(parents=True, exist_ok=True)
    REQ.write_text(req_new, encoding="utf-8", newline="\n")

    verify = MAIN.read_text(encoding="utf-8")
    if NEW_IMPORT not in verify or NEW_ROUTER not in verify:
        print("ERROR: router registration verification failed.")
        return 6

    shutil.rmtree(PAYLOAD)

    print("AIR-1.4B Canonical Sentinel-5P Satellite Field API v0.1.1 installed.")
    print("REAL API: GET /air/satellite-field")
    print("Canonical latitude order: ascending")
    print("Coordinates: pixel centres")
    print("Invalid TROPOMI pixels: JSON null")
    print("Negative valid retrievals: preserved")
    print("Stride: 1..8, no interpolation")
    print("Statistics: full valid source grid + returned-grid stats")
    print("Semantics: satellite observation, NOT surface concentration")
    print("Dependency recorded: rasterio>=1.5.1,<2")
    print("Added:")
    for item in installed:
        print(f"  {item}")
    print("Modified:")
    print("  backend\\main.py")
    print("  backend\\requirements-air.txt")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
