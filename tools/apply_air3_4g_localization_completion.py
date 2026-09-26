from pathlib import Path

root = Path("frontend/src")

# This patch replaces hardcoded visible strings with translation helper calls
# where the current files contain direct literals.

replacements = {
    "shareIncidentSummary.js": [
        ("Incident Summary", "t(currentLanguage, 'incidentSummary.title')"),
        ("Evidence:", "t(currentLanguage, 'incidentSummary.evidence') + ':'"),
        ("Timeline:", "t(currentLanguage, 'incidentSummary.timeline') + ':'"),
        ("Impact:", "t(currentLanguage, 'incidentSummary.impact') + ':'"),
        ("Not calculated", "t(currentLanguage, 'incidentSummary.notCalculated')"),
    ],
    "sourceOverviewBlock.js": [
        ("Data Sources", "t(currentLanguage, 'sources.title')"),
        ("Satellite", "t(currentLanguage, 'sources.satellite')"),
        ("Model", "t(currentLanguage, 'sources.model')"),
        ("Simulation", "t(currentLanguage, 'sources.simulation')"),
    ],
    "main.js": [
        ("Impact Forecast", "t(currentLanguage, 'impact.title')"),
        ("Targets", "t(currentLanguage, 'impact.targets')"),
    ],
}

for filename, items in replacements.items():
    path = root / filename
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")

    for old, new in items:
        if old in text:
            text = text.replace(old, new, 1)

    path.write_text(text, encoding="utf-8")

print("AIR-3.4G localization completion patch applied")
