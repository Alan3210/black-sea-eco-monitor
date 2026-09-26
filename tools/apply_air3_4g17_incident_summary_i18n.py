from pathlib import Path

# Add incident summary keys to i18n.js
i18n = Path("frontend/src/i18n.js")
text = i18n.read_text(encoding="utf-8")

ru_block = """
    'incidentSummary.title': 'Сводка инцидента',
    'incidentSummary.evidence': 'Доказательства',
    'incidentSummary.timeline': 'Хронология',
    'incidentSummary.impact': 'Воздействие',
    'incidentSummary.notCalculated': 'Не рассчитано',
    'incidentSummary.available': 'Доступно',
    'incidentSummary.copy': 'Копировать сводку',
"""

en_block = """
    'incidentSummary.title': 'Incident Summary',
    'incidentSummary.evidence': 'Evidence',
    'incidentSummary.timeline': 'Timeline',
    'incidentSummary.impact': 'Impact',
    'incidentSummary.notCalculated': 'Not calculated',
    'incidentSummary.available': 'Available',
    'incidentSummary.copy': 'Copy Summary',
"""

if "'incidentSummary.title':" not in text:
    # Insert RU before en block, using the existing language split.
    marker = "\n\n  en: {"
    if marker not in text:
        raise SystemExit("language split marker not found")

    text = text.replace(marker, "\n" + ru_block + marker, 1)

    # Insert EN after the impact keys if possible.
    marker = "    'impact.targets': 'Targets',"
    pos = text.find(marker)
    if pos != -1:
        end = pos + len(marker)
        text = text[:end] + "\n" + en_block + text[end:]

i18n.write_text(text, encoding="utf-8")


# Update shareIncidentSummary.js
share = Path("frontend/src/shareIncidentSummary.js")
text = share.read_text(encoding="utf-8")

text = text.replace(
"""      <button>
        Copy Summary
      </button>""",
"""      <button>
        ${label('incidentSummary.copy', 'Copy Summary')}
      </button>"""
)

text = text.replace(
"""            : (summary.impact ? "Available" : "—")""",
"""            : (
              summary.impact
                ? label('incidentSummary.available', 'Available')
                : "—"
            )"""
)

share.write_text(text, encoding="utf-8")

print("AIR-3.4G17 incident summary localization applied")
