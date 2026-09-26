from pathlib import Path

ROOT = Path("frontend/src")

def apply_replacements(path, replacements):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    changed = False

    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
        print("updated", path)

# Fix literal translation calls accidentally inserted into templates.
targets = [
    (
        ROOT / "main.js",
        [
            (
                "t(currentLanguage, 'impact.title')",
                "${t(currentLanguage, 'impact.title')}",
            ),
            (
                "t(currentLanguage, 'impact.targets')",
                "${t(currentLanguage, 'impact.targets')}",
            ),
        ],
    ),
    (
        ROOT / "sourceOverviewBlock.js",
        [
            (
                "t(currentLanguage, 'sources.title')",
                "${t(currentLanguage, 'sources.title')}",
            ),
            (
                "t(currentLanguage, 'sources.satellite')",
                "${t(currentLanguage, 'sources.satellite')}",
            ),
            (
                "t(currentLanguage, 'sources.model')",
                "${t(currentLanguage, 'sources.model')}",
            ),
            (
                "t(currentLanguage, 'sources.simulation')",
                "${t(currentLanguage, 'sources.simulation')}",
            ),
        ],
    ),
]

for path, replacements in targets:
    apply_replacements(path, replacements)

print("AIR-3.4G4 localization binding patch applied")
