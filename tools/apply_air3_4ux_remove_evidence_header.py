from pathlib import Path

for filename in [
    "frontend/src/evidenceDashboardPanel.js",
    "frontend/src/evidenceDashboardRenderer.js",
]:
    path = Path(filename)
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")

    text = text.replace(
        """      <h2>Evidence Dashboard</h2>""",
        ""
    )

    text = text.replace(
        """      <h2>${t(currentLanguage, 'panel.evidenceDashboard')}</h2>""",
        ""
    )

    path.write_text(text, encoding="utf-8")

print("AIR-3.4UX remove evidence dashboard header applied")
