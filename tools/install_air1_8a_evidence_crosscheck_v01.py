from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.cwd()

def main():
    if not (ROOT / "backend" / "schemas").exists():
        raise RuntimeError("Missing backend/schemas")

    (ROOT / "dev-snapshots" / f"AIR1_8A_{datetime.now().strftime("%Y%m%d_%H%M%S")}").mkdir(
        parents=True, exist_ok=True
    )

    payload = ROOT / "payload"
    for src in payload.rglob("*"):
        if src.is_file():
            dst = ROOT / src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print("[COPY]", dst)

    shutil.rmtree(payload)

    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_evidence_crosscheck_schema.py"],
        check=True,
    )

    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
