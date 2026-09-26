from pathlib import Path

path = Path("frontend/src/shareIncidentSummary.js")
text = path.read_text(encoding="utf-8")

# Add import if absent
if "from './i18n.js'" not in text and 'from "./i18n.js"' not in text:
    text = "import { t } from './i18n.js';\n\n" + text

# Render function gets language context
text = text.replace(
    "export function renderShareSummary(summary = {}) {",
    "export function renderShareSummary(summary = {}, currentLanguage = 'ru') {"
)

replacements = {
    '<h2>t(currentLanguage, \\'incidentSummary.title\\')</h2>':
        "<h2>${t(currentLanguage, 'incidentSummary.title')}</h2>",
    "t(currentLanguage, 'incidentSummary.evidence') + ':'":
        "${t(currentLanguage, 'incidentSummary.evidence')}:",
    "t(currentLanguage, 'incidentSummary.timeline') + ':'":
        "${t(currentLanguage, 'incidentSummary.timeline')}:",
    "t(currentLanguage, 'incidentSummary.impact') + ':'":
        "${t(currentLanguage, 'incidentSummary.impact')}:",
    '"t(currentLanguage, \\'incidentSummary.notCalculated\\')"' :
        "t(currentLanguage, 'incidentSummary.notCalculated')",
}

for old, new in replacements.items():
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G2 share summary i18n fix applied")
