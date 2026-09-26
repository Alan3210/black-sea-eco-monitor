from pathlib import Path

# Fix sourceOverviewBlock metadata preservation and usage
path = Path("frontend/src/sourceOverviewBlock.js")
text = path.read_text(encoding="utf-8")

old = """    type: source.type || "unknown",
    purpose: source.purpose || "",
    status: source.status || "available","""

new = """    type: source.type || "unknown",
    typeKey: source.typeKey || null,
    purpose: source.purpose || "",
    purposeKey: source.purposeKey || null,
    status: source.status || "available","""

if old not in text:
    raise SystemExit("sourceOverview build model anchor not found")

text = text.replace(old, new, 1)

old = """<h3>${t(currentLanguage, `sources.${type.toLowerCase()}`) || type}</h3>"""

new = """<h3>${t(
          currentLanguage,
          items[0]?.typeKey || `sources.${type.toLowerCase()}`
        )}</h3>"""

if old not in text:
    raise SystemExit("sourceOverview type render anchor not found")

text = text.replace(old, new, 1)

old = """<span>${t(currentLanguage, `sources.${item.purpose.toLowerCase()}`) || item.purpose}</span>"""

new = """<span>${t(
              currentLanguage,
              item.purposeKey || `sources.${item.purpose.toLowerCase()}`
            )}</span>"""

if old not in text:
    raise SystemExit("sourceOverview purpose render anchor not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("AIR-3.4G12 source metadata preservation applied")
