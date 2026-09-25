from pathlib import Path
from datetime import datetime
import shutil, subprocess, sys

ROOT = Path.cwd()

def main():
    for item in [
        ROOT/"backend/services/eea_station_provider.py",
        ROOT/"backend/services/eea_parquet_downloader.py",
        ROOT/"backend/services/eea_station_data_loader.py",
    ]:
        if not item.exists():
            raise RuntimeError(f"Missing prerequisite: {item}")

    (ROOT/"dev-snapshots"/f"AIR1_6E2C3A_{datetime.now().strftime("%Y%m%d_%H%M%S")}").mkdir(parents=True, exist_ok=True)

    payload = ROOT/"payload"
    for src in payload.rglob("*"):
        if src.is_file():
            dst = ROOT/src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    shutil.rmtree(payload)

    subprocess.run([sys.executable, "-m", "pytest", "tests/test_eea_station_refresh_pipeline.py"], check=True)

if __name__ == "__main__":
    main()
