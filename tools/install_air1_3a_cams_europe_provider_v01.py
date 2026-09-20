from pathlib import Path
import importlib.metadata, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = ROOT / ".gitignore"
CACHE_RULE = "data/cache/air/"

def ensure_dependency():
    try:
        print("cdsapi already installed:", importlib.metadata.version("cdsapi"))
        return
    except importlib.metadata.PackageNotFoundError:
        pass
    print("Installing cdsapi>=0.7.7 into active Python environment...")
    subprocess.run([sys.executable, "-m", "pip", "install", "cdsapi>=0.7.7"], check=True)

def ensure_gitignore():
    text = GITIGNORE.read_text(encoding="utf-8") if GITIGNORE.exists() else ""
    if CACHE_RULE in {x.strip() for x in text.splitlines()}: return
    snap = ROOT / "dev-snapshots"; snap.mkdir(parents=True, exist_ok=True)
    if GITIGNORE.exists(): shutil.copy2(GITIGNORE, snap / ".gitignore.before_air1_3a")
    if text and not text.endswith("\n"): text += "\n"
    GITIGNORE.write_text(text + "\n# AIR runtime cache\n" + CACHE_RULE + "\n", encoding="utf-8", newline="\n")

def main():
    ensure_dependency(); ensure_gitignore()
    print("AIR-1.3A CAMS Europe Provider v0.1 installed.")
    print("Provider: CAMS Europe ensemble forecast")
    print("Cache: data/cache/air/cams-europe")
    print("Primary species: PM2.5, PM10, NO2, SO2, O3")
    print("Dust is available but tagged experimental.")
    print("No FastAPI endpoint or Web GIS layer added yet.")
    print("Before live retrieval, configure ~/.cdsapirc and accept the CAMS dataset licence in ADS.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
