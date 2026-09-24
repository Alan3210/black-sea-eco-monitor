from pathlib import Path
import shutil, subprocess, sys
from datetime import datetime

ROOT=Path.cwd()

def main():
    for p in [
        ROOT/"backend/services/eea_metadata_provider.py",
        ROOT/"backend/services/eea_station_field.py",
    ]:
        if not p.exists():
            raise RuntimeError(f"Missing prerequisite: {p}")

    (ROOT/"dev-snapshots"/f"AIR1_6D4A_{datetime.now().strftime('%Y%m%d_%H%M%S')}").mkdir(parents=True, exist_ok=True)

    payload=ROOT/"payload"
    for src in payload.rglob("*"):
        if src.is_file():
            dst=ROOT/src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src,dst)

    shutil.rmtree(payload)

    subprocess.run(
        [sys.executable,"-m","pytest","tests/test_eea_measurement_parser.py"],
        check=True
    )

    print("INSTALL COMPLETE")

if __name__=="__main__":
    main()
