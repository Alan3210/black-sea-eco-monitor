from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_5a_payload"

FILES = [
    (
        PAYLOAD / "backend/services/geos_cf_provider.py",
        ROOT / "backend/services/geos_cf_provider.py",
    ),
    (
        PAYLOAD / "tests/test_geos_cf_provider.py",
        ROOT / "tests/test_geos_cf_provider.py",
    ),
    (
        PAYLOAD / "tools/air1_5a_geos_cf_probe.py",
        ROOT / "tools/air1_5a_geos_cf_probe.py",
    ),
]

REQ = ROOT / "backend/requirements-air.txt"
PYDAP_REQ = "pydap>=3.5,<4"


def patch_requirements(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    if not any(
        line.strip().lower().startswith("pydap")
        for line in lines
    ):
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(PYDAP_REQ)
    return "\n".join(lines).rstrip() + "\n"


def backup(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    target = backup_root / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def main() -> int:
    missing = [str(src) for src, _ in FILES if not src.exists()]
    if missing:
        print("ERROR: AIR-1.5A payload incomplete:")
        for item in missing:
            print(f"  {item}")
        return 2

    req_old = REQ.read_text(encoding="utf-8") if REQ.exists() else ""
    req_new = patch_requirements(req_old)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_5a_before_apply_{stamp}"
    )

    backup(REQ, backup_root)
    for _, dst in FILES:
        backup(dst, backup_root)

    installed = []
    for src, dst in FILES:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        installed.append(dst.relative_to(ROOT))

    REQ.parent.mkdir(parents=True, exist_ok=True)
    REQ.write_text(req_new, encoding="utf-8", newline="\n")

    shutil.rmtree(PAYLOAD)

    print("AIR-1.5A NASA GEOS-CF v2 Provider v0.1 installed.")
    print("Source: NASA GMAO / NCCS public OPeNDAP")
    print("Dataset: GEOS-CF v2 forecast AQC hourly-average surface layer")
    print("Global native grid: 0.25 degrees")
    print("Default Black Sea subset: [26.0, 39.0, 43.5, 48.0]")
    print("Products: PM2.5, PM10, NO2, SO2, O3, CO")
    print("PM products: native mass concentration, ug/m3")
    print("Gas products: native dry-air mole fraction, mol/mol")
    print("Semantics: research model forecast, NOT observation")
    print("Cache: run-scoped JSON field cache")
    print("Dependency recorded: pydap>=3.5,<4")
    print("Added:")
    for item in installed:
        print(f"  {item}")
    print("Modified:")
    print("  backend\\requirements-air.txt")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
