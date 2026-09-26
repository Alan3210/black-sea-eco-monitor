from pathlib import Path

target = Path("frontend/src/incidentReportExport.js")

text = target.read_text(encoding="utf-8")

old = "<h2>${report.title}</h2>"
new = "<h2>Incident Report</h2>\\n      <h3>${report.title}</h3>"

if old not in text:
    raise SystemExit("Target string not found. Patch not applied.")

target.write_text(
    text.replace(old, new, 1),
    encoding="utf-8",
)

print("AIR-3.2C1 patch applied")
