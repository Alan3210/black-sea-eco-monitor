from pathlib import Path

path = Path("frontend/src/i18n.js")
text = path.read_text(encoding="utf-8")

block = """
    'incidentSummary.title': 'Сводка инцидента',
    'incidentSummary.evidence': 'Доказательства',
    'incidentSummary.timeline': 'Хронология',
    'incidentSummary.impact': 'Воздействие',
    'incidentSummary.notCalculated': 'Не рассчитано',
    'incidentSummary.available': 'Доступно',
    'incidentSummary.copy': 'Копировать сводку',
"""

# Remove misplaced top-level RU block fragment if it exists between ru and en.
start = text.find("    'incidentSummary.title':")
en_pos = text.find("  en: {")

if start != -1 and en_pos != -1 and start < en_pos:
    end = text.find("\n\n\n  en: {", start)
    if end == -1:
        end = en_pos
    misplaced = text[start:end]
    if "'incidentSummary.title'" in misplaced:
        text = text[:start] + text[end:]

# Insert into RU block before the ru closing brace.
marker = "    'timeline.evidenceUpdate': 'Обновление доказательств',"

if marker in text and "'incidentSummary.title': 'Сводка инцидента'" not in text[:text.find("  en: {")]:
    text = text.replace(marker, marker + "\n" + block, 1)

path.write_text(text, encoding="utf-8")

# Remove temporary runtime debug if still present
share = Path("frontend/src/shareIncidentSummary.js")
if share.exists():
    s = share.read_text(encoding="utf-8")
    s = s.replace(
"""  console.log(
    "INCIDENT I18N CHECK",
    currentLanguage,
    t(currentLanguage, "incidentSummary.title"),
    t(currentLanguage, "incidentSummary.evidence"),
  );

""", ""
    )
    s = s.replace(
"""  console.log(
    "SHARE SUMMARY LANGUAGE",
    currentLanguage
  );

""", ""
    )
    share.write_text(s, encoding="utf-8")

print("AIR-3.4G19 translation scope final cleanup applied")
