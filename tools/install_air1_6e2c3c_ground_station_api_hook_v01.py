from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.cwd()

def main():
    required = [
        ROOT / "backend/services/ground_station_service.py",
        ROOT / "backend/services/eea_station_refresh_service.py",
    ]

    for item in required:
        if not item.exists():
            raise RuntimeError(f"Missing prerequisite: {item}")

    (ROOT / "dev-snapshots" / f"AIR1_6E2C3C_{datetime.now().strftime('%Y%m%d_%H%M%S')}").mkdir(
        parents=True, exist_ok=True
    )

    payload = ROOT / "payload"
    for src in payload.rglob("*"):
        if src.is_file():
            dst = ROOT / src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    shutil.rmtree(payload)

    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_ground_station_api_real.py"],
        check=True,
    )

    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
