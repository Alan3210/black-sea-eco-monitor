from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.cwd()

def main():
    for p in [
        ROOT/"backend/services/eea_station_provider.py",
        ROOT/"backend/schemas/station.py",
    ]:
        if not p.exists():
            raise RuntimeError(f"Missing prerequisite: {p}")

    payload = ROOT/"payload"
    for src in payload.rglob("*"):
        if src.is_file():
            dst = ROOT/src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    shutil.rmtree(payload)

    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_eea_metadata_provider.py"],
        check=True
    )

    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
