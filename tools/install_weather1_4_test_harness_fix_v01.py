from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "frontend" / "src" / "driftForcing.test.js"
SOURCE = REPO_ROOT / "frontend" / "src" / "driftForcing.test.fixed.js"


def main() -> int:
    if not SOURCE.exists():
        print(f"ERROR: fix source missing: {SOURCE}")
        return 2

    TARGET.write_text(
        SOURCE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    SOURCE.unlink()

    print("WEATHER-1.4 test harness fix installed.")
    print("Modified:")
    print("  frontend/src/driftForcing.test.js")
    print("Runtime application files were not modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
