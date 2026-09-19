from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5d2_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/index.html": "6ec70296c7e87037225f24074a20acd303cb939f88a1d75c5ea3dff2369dbaeb",
    "frontend/src/style.css": "cd4f87e30d24bc26a9ca13ad5d90a33e1fdf9d957091b7d7b767f0c84e0a5b66",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def cleanup_payload() -> None:
    if PAYLOAD_ROOT.exists():
        shutil.rmtree(
            PAYLOAD_ROOT,
        )


def main() -> int:
    index_path = (
        REPO_ROOT
        / "frontend"
        / "index.html"
    )

    if index_path.exists():
        current = index_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if (
            "combined-fields-hud--header"
            in current
            and current.count(
                'id="combined-fields-hud"'
            ) == 1
        ):
            cleanup_payload()
            print(
                "WEATHER-1.5D.2 Header-Integrated Operational Status v0.1 already installed."
            )
            return 0

    missing = []

    for rel in TARGETS:
        if not (
            REPO_ROOT / rel
        ).exists():
            missing.append(
                rel
            )

        if not (
            PAYLOAD_ROOT / rel
        ).exists():
            missing.append(
                f".weather1_5d2_payload/{rel}"
            )

    if missing:
        print(
            "ERROR: required files are missing:"
        )

        for rel in missing:
            print(
                f"  {rel}"
            )

        return 2

    mismatches = []

    for rel, expected in TARGETS.items():
        actual = sha256(
            REPO_ROOT / rel
        )

        if actual != expected:
            mismatches.append(
                (
                    rel,
                    expected,
                    actual,
                )
            )

    if mismatches:
        print(
            "ERROR: frontend does not match the clean WEATHER-1.5D baseline."
        )
        print(
            "This patch must be applied BEFORE WEATHER-1.5D.1."
        )
        print(
            "No tracked files were modified."
        )

        for (
            rel,
            expected,
            actual,
        ) in mismatches:
            print(
                f"  {rel}"
            )
            print(
                f"    expected: {expected}"
            )
            print(
                f"    actual:   {actual}"
            )

        return 3

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backups = {}

    for rel in TARGETS:
        source = REPO_ROOT / rel
        safe_name = (
            rel
            .replace("/", "_")
            .replace("\\", "_")
        )

        backup = (
            BACKUP_DIR
            / (
                f"{safe_name}"
                f".before_weather1_5d2_"
                f"{stamp}"
            )
        )

        shutil.copy2(
            source,
            backup,
        )

        backups[rel] = backup

    try:
        for rel in TARGETS:
            shutil.copy2(
                PAYLOAD_ROOT / rel,
                REPO_ROOT / rel,
            )
    except Exception:
        for rel, backup in backups.items():
            shutil.copy2(
                backup,
                REPO_ROOT / rel,
            )
        raise

    cleanup_payload()

    print(
        "WEATHER-1.5D.2 Header-Integrated Operational Status v0.1 installed."
    )
    print(
        "Changed:"
    )
    print(
        "  combined wind/current status moved into the fixed top bar"
    )
    print(
        "  floating map HUD removed"
    )
    print(
        "  responsive compact field/source/time/Delta-t presentation added"
    )
    print(
        "No JavaScript logic, backend APIs, ECMWF, Copernicus, OpenDrift, or model physics were modified."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
