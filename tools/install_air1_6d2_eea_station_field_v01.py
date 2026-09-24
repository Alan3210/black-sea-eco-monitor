from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.cwd()
SNAPSHOT = ROOT / "dev-snapshots" / f"AIR1_6D2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def verify():
    required = [
        ROOT / "backend" / "services" / "eea_station_provider.py",
        ROOT / "backend" / "schemas" / "station.py",
    ]
    for item in required:
        if not item.exists():
            raise RuntimeError(f"Missing prerequisite: {item}")
    print("[OK] prerequisites")

def backup():
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    for item in [
        ROOT / "backend" / "services" / "eea_station_provider.py",
        ROOT / "backend" / "schemas" / "station.py",
    ]:
        shutil.copy2(item, SNAPSHOT / item.name)
    print("[OK] backup:", SNAPSHOT)

def install():
    payload = ROOT / "payload"
    if not payload.exists():
        raise RuntimeError("payload folder missing")

    for src in payload.rglob("*"):
        if src.is_file():
            dst = ROOT / src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print("[COPY]", dst)

    shutil.rmtree(payload)
    print("[OK] payload cleanup")

def verify_tests():
    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_eea_station_field.py"],
        check=True
    )

def main():
    print("=== AIR-1.6D2 EEA Station Field Adapter installer ===")
    verify()
    backup()
    install()
    verify_tests()
    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
