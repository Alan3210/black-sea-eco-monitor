from pathlib import Path

path = Path("frontend/src/evidenceTimelineUX.js")
text = path.read_text(encoding="utf-8")

if "import { t } from './i18n.js';" not in text:
    text = "import { t } from './i18n.js';\n\n" + text

text = text.replace(
    "export function renderVerticalTimeline(events = []) {",
    """export function renderVerticalTimeline(
  events = [],
  currentLanguage = 'ru'
) {"""
)

old = '<strong>${event.title || "Evidence event"}</strong>'
new = """<strong>${
          event.i18nKey
            ? t(currentLanguage, event.i18nKey)
            : event.title || "Evidence event"
        }</strong>"""

if old in text:
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

# Patch main.js call if exact closing exists
main = Path("frontend/src/main.js")
mtext = main.read_text(encoding="utf-8")

old = """        time: '13.09 10:54',
      },
    ]);"""

new = """        time: '13.09 10:54',
      },
    ], currentLanguage);"""

if old in mtext:
    mtext = mtext.replace(old, new, 1)

main.write_text(mtext, encoding="utf-8")

print("AIR-3.4G14 timeline renderer localization applied")
