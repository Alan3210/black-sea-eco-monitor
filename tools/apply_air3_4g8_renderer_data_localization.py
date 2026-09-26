from pathlib import Path

# sourceOverviewBlock
path = Path("frontend/src/sourceOverviewBlock.js")
text = path.read_text(encoding="utf-8")

if "import { t }" not in text and 'import { t }' not in text:
    text = "import { t } from './i18n.js';\n\n" + text

text = text.replace(
    "export function renderSourceOverview(sources = []) {",
    "export function renderSourceOverview(sources = [], currentLanguage = 'ru') {"
)

text = text.replace(
    "<h3>${type}</h3>",
    "<h3>${t(currentLanguage, `sources.${type.toLowerCase()}`) || type}</h3>"
)

text = text.replace(
    "<span>${item.purpose}</span>",
    "<span>${t(currentLanguage, `sources.${item.purpose.toLowerCase()}`) || item.purpose}</span>"
)

path.write_text(text, encoding="utf-8")


# evidenceTimelineRenderer
path = Path("frontend/src/evidenceTimelineRenderer.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "<strong>${event.title}</strong>",
    "<strong>${event.i18nKey ? t(currentLanguage, event.i18nKey) : event.title}</strong>"
)

path.write_text(text, encoding="utf-8")

print("AIR-3.4G8 renderer data localization patch applied")
