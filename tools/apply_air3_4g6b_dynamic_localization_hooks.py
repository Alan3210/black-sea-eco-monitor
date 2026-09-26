from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

old = """    <div class=\"detail-section__title\">
      ${t(currentLanguage, 'impact.title')}
    </div>"""

new = """    <div
      class=\"detail-section__title\"
      data-i18n=\"impact.title\"
    >
      ${t(currentLanguage, 'impact.title')}
    </div>"""

if old in text:
    text = text.replace(old, new, 1)

old = """        <div class=\"detail-metric__label\">
          ${t(currentLanguage, 'impact.targets')}
        </div>"""

new = """        <div
          class=\"detail-metric__label\"
          data-i18n=\"impact.targets\"
        >
          ${t(currentLanguage, 'impact.targets')}
        </div>"""

if old in text:
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G6B dynamic localization hooks applied")
