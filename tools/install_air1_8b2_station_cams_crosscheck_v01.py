from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path.cwd()

def main():
    required = [
        ROOT / "backend" / "schemas" / "evidence_crosscheck.py",
        ROOT / "backend" / "services" / "cams_evidence_adapter.py",
    ]

    for item in required:
        if not item.exists():
            raise RuntimeError(f"Missing prerequisite: {item}")

    (ROOT / "dev-snapshots" / f"AIR1_8B2_{datetime.now().strftime('%Y%m%d_%H%M%S')}").mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = ROOT / "payload"
    for src in payload.rglob("*"):
        if src.is_file():
            dst = ROOT / src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    shutil.rmtree(payload)

    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_evidence_crosscheck_service.py"],
        check=True,
    )

    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
