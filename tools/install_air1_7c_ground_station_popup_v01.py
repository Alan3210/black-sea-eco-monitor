from pathlib import Path
import shutil, subprocess

ROOT=Path.cwd()

def main():
    payload=ROOT/"payload"
    for src in payload.rglob("*"):
        if src.is_file():
            dst=ROOT/src.relative_to(payload)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src,dst)
    shutil.rmtree(payload)
    subprocess.run(["cmd","/c","npm","test"], cwd=ROOT/"frontend", check=True)
    print("INSTALL COMPLETE")

if __name__=="__main__":
    main()
