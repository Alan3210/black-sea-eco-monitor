from pathlib import Path
import re

path = Path("frontend/src/i18n.js")
text = path.read_text(encoding="utf-8")

keys = [
    "impact.title",
    "impact.targets",
    "sources.title",
    "sources.satellite",
    "sources.model",
    "sources.simulation",
    "panel.evidenceDashboard",
    "sources.observation",
    "sources.forecast",
    "sources.prediction",
    "timeline.title",
    "timeline.satelliteObservation",
    "timeline.camsForecast",
    "timeline.eventDetected",
    "timeline.evidenceUpdate",
]

# Find accidental top-level block between the end of ru and the start of en.
start = text.find("    'impact.title'")
end = text.find("  en: {")

if start != -1 and end != -1 and start < end:
    misplaced = text[start:end]
    text = text[:start] + text[end:]

    # Extract lines with translation entries
    entries = "\n".join(
        line for line in misplaced.splitlines()
        if any("'" + key + "'" in line for key in keys)
    )

    # Insert into ru before its closing brace near the beginning section.
    ru_marker = "\n  },\n  en: {"
    if ru_marker in text:
        text = text.replace(
            ru_marker,
            "\n" + entries + "\n  },\n  en: {",
            1
        )

    # Build English equivalents if they are also misplaced or missing is handled manually.
    en_entries = """
    'impact.title': 'Impact Forecast',
    'impact.targets': 'Targets',
    'sources.title': 'Data Sources',
    'sources.satellite': 'Satellite',
    'sources.model': 'Model',
    'sources.simulation': 'Simulation',
    'panel.evidenceDashboard': 'Evidence Dashboard',
    'sources.observation': 'Observation',
    'sources.forecast': 'Forecast',
    'sources.prediction': 'Prediction',
    'timeline.title': 'Evidence Timeline',
    'timeline.satelliteObservation': 'Satellite observation',
    'timeline.camsForecast': 'CAMS forecast',
    'timeline.eventDetected': 'Event detected',
    'timeline.evidenceUpdate': 'Evidence update',
""".strip()

    # Insert before final closing of en object
    final = text.rfind("\n  },\n};")
    if final != -1 and "'timeline.evidenceUpdate': 'Evidence update'" not in text[text.find("  en: {"):final]:
        text = text[:final] + "\n" + en_entries + text[final:]

path.write_text(text, encoding="utf-8")
print("AIR-3.4G13 translation scope fix applied")
