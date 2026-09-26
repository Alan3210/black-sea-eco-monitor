from pathlib import Path

path = Path("frontend/src/shareIncidentSummary.js")
text = path.read_text(encoding="utf-8")

old = '    location: report.location || "Unknown",'
new = '    location: report.location || null,'

if old not in text:
    raise SystemExit("Location fallback not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4F3 location fallback fix applied")
