from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
"""      Data Sources
    </div>
    ${renderSourceOverview([""",
"""      ${t(currentLanguage, 'sources.title')}
    </div>
    ${renderSourceOverview([""",
1
)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G6A source overview i18n fix applied")
