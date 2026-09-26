from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

old = """      }),
    );

  const impactForecastSection"""

new = """      }),
      currentLanguage,
    );

  const impactForecastSection"""

if old not in text:
    raise SystemExit("share summary language anchor not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("AIR-3.4G18 share summary language propagation applied")
