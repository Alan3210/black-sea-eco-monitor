from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

old = """        timeline: [
          {
            title: "Evidence Timeline",
          },
        ],"""

new = """        timeline: [
          {
            title: "Satellite observation",
          },
          {
            title: "CAMS forecast",
          },
          {
            title: "Event detected",
          },
          {
            title: "Evidence update",
          },
        ],"""

if old in text:
    text = text.replace(old, new, 1)
else:
    print("Timeline placeholder not found; no replacement made")

path.write_text(text, encoding="utf-8")
print("AIR-3.4E timeline binding patch applied")
