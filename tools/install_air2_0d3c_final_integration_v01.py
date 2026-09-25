from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path.cwd()

def main():
    payload = ROOT / "payload"

    if payload.exists():
        for src in payload.rglob("*"):
            if src.is_file():
                dst = ROOT / src.relative_to(payload)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print("[COPY]", dst)
        shutil.rmtree(payload)

    print("Running backend tests...")
    subprocess.run(
        [sys.executable, "-m", "pytest"],
        check=True,
    )

    frontend = ROOT / "frontend"
    if frontend.exists():
        subprocess.run(
            ["cmd", "/c", "npm", "test"],
            cwd=frontend,
            check=True,
        )

    print("INSTALL COMPLETE")

if __name__ == "__main__":
    main()
