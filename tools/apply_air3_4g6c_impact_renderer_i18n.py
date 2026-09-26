from pathlib import Path

files = [
    Path("frontend/src/impactSummaryUX.js"),
    Path("frontend/src/impactForecastResult.js"),
]

for path in files:
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")

    if "import { t }" not in text and 'import { t }' not in text:
        text = "import { t } from './i18n.js';\n\n" + text

    text = text.replace(
        "export function renderImpactSummaryUX(state = {}) {",
        "export function renderImpactSummaryUX(state = {}, currentLanguage = 'ru') {"
    )

    text = text.replace(
        "export function renderImpactForecastSummary(vm = {}) {",
        "export function renderImpactForecastSummary(vm = {}, currentLanguage = 'ru') {"
    )

    text = text.replace(
        "Impact Forecast",
        "${t(currentLanguage, 'impact.title')}"
    )

    text = text.replace(
        "Potential impact",
        "${t(currentLanguage, 'impact.potential')}"
    )

    text = text.replace(
        "Affected areas",
        "${t(currentLanguage, 'impact.affectedAreas')}"
    )

    text = text.replace(
        "Closest distance",
        "${t(currentLanguage, 'impact.closestDistance')}"
    )

    text = text.replace(
        "First exposure",
        "${t(currentLanguage, 'impact.firstExposure')}"
    )

    path.write_text(text, encoding="utf-8")

print("AIR-3.4G6C impact renderer localization patch applied")
