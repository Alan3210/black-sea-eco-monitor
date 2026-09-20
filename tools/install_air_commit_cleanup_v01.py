
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

remove_target = ROOT / "air_field_response.json"

if remove_target.exists():
    remove_target.unlink()
    print("Removed air_field_response.json")
else:
    print("air_field_response.json already absent")

gitignore = ROOT / ".gitignore"

text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""

rules = [
    "data/cache/air/",
    "validation/air1_3a1_cams_netcdf_inspection.json",
    "air_field_response.json",
]

changed = False

for rule in rules:
    if rule not in text.splitlines():
        if text and not text.endswith("\n"):
            text += "\n"
        text += rule + "\n"
        changed = True

if changed or not gitignore.exists():
    gitignore.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print("Updated .gitignore")
else:
    print(".gitignore already contains AIR exclusions")

print("AIR-COMMIT-CLEANUP v0.1 complete.")
print("Ready for git add / commit.")
