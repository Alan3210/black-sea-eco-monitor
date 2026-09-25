from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path.cwd()

def main():
    if not (ROOT / "backend" / "api").exists():
        raise RuntimeError("Missing backend/api")

    (ROOT / "dev-snapshots" / f"AIR1_8D1A_{datetime.now().strftime("%Y%m%d_%H%M%S")}").mkdir(
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
        [sys.executable, "-m", "pytest", "tests/test_evidence_crosscheck_api.py"],
        check=True,
    )

    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
