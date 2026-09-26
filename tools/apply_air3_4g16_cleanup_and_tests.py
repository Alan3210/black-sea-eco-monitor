from pathlib import Path

# Remove temporary diagnostic logs from sourceOverviewBlock
path = Path("frontend/src/sourceOverviewBlock.js")
text = path.read_text(encoding="utf-8")

for block in [
"""  console.log(
    "SOURCE INPUT",
    JSON.stringify(sources, null, 2),
    "LANG",
    currentLanguage
  );
""",
"""  console.log(
    "GROUPS",
    JSON.stringify(groups, null, 2)
  );
""",
"""  console.log(
    "FINAL TRANSLATION CHECK",
    key,
    t(currentLanguage, key)
  );
"""
]:
    text = text.replace(block, "")

path.write_text(text, encoding="utf-8")

# Update impact tests to explicitly test EN renderer output
for filename, old in [
    ("frontend/src/impactForecastResult.test.js",
     "renderImpactForecastSummary(vm)"),
    ("frontend/src/impactSummaryUX.test.js",
     "renderImpactSummaryUX(state)")
]:
    path = Path(filename)
    if path.exists():
        text = path.read_text(encoding="utf-8")
        text = text.replace(old, old[:-1] + ", 'en')")
        path.write_text(text, encoding="utf-8")

print("AIR-3.4G16 cleanup and impact tests compatibility applied")
