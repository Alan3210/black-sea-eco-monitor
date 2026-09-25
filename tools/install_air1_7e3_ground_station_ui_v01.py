from pathlib import Path
from datetime import datetime
import shutil
import subprocess

ROOT = Path.cwd()

def main():
    if not (ROOT / "frontend" / "src").exists():
        raise RuntimeError("Missing frontend/src")

    (ROOT / "dev-snapshots" / f"AIR1_7E3_{datetime.now().strftime("%Y%m%d_%H%M%S")}").mkdir(
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
        ["cmd", "/c", "npm", "test"],
        cwd=ROOT / "frontend",
        check=True,
    )

    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
