from pathlib import Path

path = Path("frontend/src/shareIncidentSummary.js")
text = path.read_text(encoding="utf-8")

if "from './i18n.js'" not in text and 'from "./i18n.js"' not in text:
    text = "import { t } from './i18n.js';\n\n" + text

text = text.replace(
    "export function renderShareSummary(summary = {}) {",
    "export function renderShareSummary(summary = {}, currentLanguage = 'ru') {"
)

text = text.replace(
    "<h2>t(currentLanguage, 'incidentSummary.title')</h2>",
    "<h2>${t(currentLanguage, 'incidentSummary.title')}</h2>"
)

text = text.replace(
    "t(currentLanguage, 'incidentSummary.evidence') + ':'",
    "${t(currentLanguage, 'incidentSummary.evidence')}:"
)

text = text.replace(
    "t(currentLanguage, 'incidentSummary.timeline') + ':'",
    "${t(currentLanguage, 'incidentSummary.timeline')}:"
)

text = text.replace(
    "t(currentLanguage, 'incidentSummary.impact') + ':'",
    "${t(currentLanguage, 'incidentSummary.impact')}:"
)

text = text.replace(
    '"t(currentLanguage, \'incidentSummary.notCalculated\')"',
    "t(currentLanguage, 'incidentSummary.notCalculated')"
)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G2 fix2 share summary i18n fix applied")
