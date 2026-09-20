
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "vite.config.js"

WEATHER_BLOCK = """      '/weather': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
"""

AIR_BLOCK = """      '/air': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
"""


def main() -> int:
    if not TARGET.exists():
        print("ERROR: frontend/vite.config.js not found.")
        return 2

    text = TARGET.read_text(
        encoding="utf-8",
    )

    if "'/air':" in text:
        print(
            "AIR-1.3C.8.5 Vite Air Proxy Fix v0.1 already installed."
        )
        return 0

    if WEATHER_BLOCK not in text:
        print(
            "ERROR: expected /weather proxy anchor not found."
        )
        print(
            "No files modified."
        )
        return 3

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup = (
        ROOT
        / "dev-snapshots"
        / f"air1_3c8_5_before_proxy_{stamp}"
        / "frontend"
        / "vite.config.js"
    )

    backup.parent.mkdir(
        parents=True,
        exist_ok=False,
    )

    shutil.copy2(
        TARGET,
        backup,
    )

    updated = text.replace(
        WEATHER_BLOCK,
        WEATHER_BLOCK + AIR_BLOCK,
        1,
    )

    TARGET.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    verify = TARGET.read_text(
        encoding="utf-8",
    )

    if "'/air':" not in verify:
        shutil.copy2(
            backup,
            TARGET,
        )
        print(
            "ERROR: /air proxy verification failed; backup restored."
        )
        return 4

    print(
        "AIR-1.3C.8.5 Vite Air Proxy Fix v0.1 installed."
    )
    print(
        "Added Vite proxy: /air -> http://127.0.0.1:8000"
    )
    print(
        "Backup:"
    )
    print(
        backup.parent.parent
    )
    print(
        "Restart Vite after this change."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
