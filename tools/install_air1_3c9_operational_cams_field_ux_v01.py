
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / ".air1_3c9_payload"

FILES = (
    "frontend/index.html",
    "frontend/src/main.js",
    "frontend/src/style.css",
    "frontend/src/i18n.js",
    "frontend/src/camsAirOperationalField.js",
    "frontend/src/camsAirOperationalField.test.js",
)


def main() -> int:
    for rel in FILES:
        if not (PAYLOAD / rel).exists():
            print(f"ERROR: missing payload: {rel}")
            return 2

    current_main = (
        ROOT / "frontend/src/main.js"
    ).read_text(encoding="utf-8")

    current_index = (
        ROOT / "frontend/index.html"
    ).read_text(encoding="utf-8")

    for marker in (
        "installCamsAirLayer",
        "refreshCamsAir",
        "CAMS_RUNTIME_CONFIG",
    ):
        if marker not in current_main:
            print(
                f"ERROR: expected CAMS runtime marker missing: {marker}"
            )
            return 3

    for marker in (
        "cams-air-layer-toggle",
        "cams-air-pollutant",
        "cams-air-panel",
    ):
        if marker not in current_index:
            print(
                f"ERROR: expected CAMS DOM marker missing: {marker}"
            )
            return 4

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup_root = (
        ROOT
        / "dev-snapshots"
        / f"air1_3c9_before_apply_{stamp}"
    )
    backup_root.mkdir(
        parents=True,
        exist_ok=False,
    )

    for rel in FILES:
        target = ROOT / rel

        if target.exists():
            backup = backup_root / rel
            backup.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            shutil.copy2(
                target,
                backup,
            )

    try:
        for rel in FILES:
            source = PAYLOAD / rel
            target = ROOT / rel
            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            shutil.copy2(
                source,
                target,
            )

        checks = {
            "frontend/index.html":
                "cams-air-operational",
            "frontend/src/main.js":
                "AIR-1.3C.9 · operational CAMS field",
            "frontend/src/style.css":
                "AIR-1.3C.9 · Operational CAMS concentration field",
            "frontend/src/i18n.js":
                "air.readyDetailed",
        }

        for rel, marker in checks.items():
            if marker not in (
                ROOT / rel
            ).read_text(
                encoding="utf-8"
            ):
                raise RuntimeError(
                    f"verification failed: {rel}"
                )

    except Exception:
        for rel in FILES:
            target = ROOT / rel
            backup = backup_root / rel

            if backup.exists():
                shutil.copy2(
                    backup,
                    target,
                )
            elif target.exists():
                target.unlink()

        raise

    shutil.rmtree(PAYLOAD)

    print(
        "AIR-1.3C.9 Operational CAMS Field UX v0.1 installed."
    )
    print(
        "REAL production mutation: APPLIED"
    )
    print(
        "Visualization: concentration grid cells (not density heatmap)"
    )
    print(
        "Added: MIN/MEAN/MAX, numeric legend, opacity control, click popup"
    )
    print(
        "Semantics: CAMS = model forecast, not ground-station observation"
    )
    print("Backup:")
    print(backup_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
