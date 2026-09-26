from pathlib import Path

path = Path("frontend/src/shareIncidentSummary.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "export function renderShareSummary(summary = {}, currentLanguage = 'ru') {",
    "export function renderShareSummary(summary = {}, currentLanguage = null) {"
)

old = """  return `
    <section class="share-summary">
      <h2>${t(currentLanguage, 'incidentSummary.title')}</h2>"""

new = """  const label = (key, fallback) =>
    currentLanguage
      ? t(currentLanguage, key)
      : fallback;

  return `
    <section class="share-summary">
      <h2>${label('incidentSummary.title', 'Incident Summary')}</h2>"""

if old in text:
    text = text.replace(old, new, 1)

replacements = {
    "${t(currentLanguage, 'incidentSummary.evidence')}:": "${label('incidentSummary.evidence', 'Evidence')}:",
    "${t(currentLanguage, 'incidentSummary.timeline')}:": "${label('incidentSummary.timeline', 'Timeline')}:",
    "${t(currentLanguage, 'incidentSummary.impact')}:": "${label('incidentSummary.impact', 'Impact')}:",
    "t(currentLanguage, 'incidentSummary.notCalculated')": "label('incidentSummary.notCalculated', 'Not calculated')",
}

for old, new in replacements.items():
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G3 share summary i18n compatibility fix applied")
