from pathlib import Path

path = Path("frontend/src/shareIncidentSummary.js")
text = path.read_text(encoding="utf-8")

old = """      <div>Location: ${summary.location}</div>
      <div>Evidence: ${summary.evidenceCount}</div>
      <div>Timeline: ${summary.timelineCount}</div>
      <div>
        Impact:
        ${summary.impact ? "Available" : "—"}
      </div>"""

new = """      ${
        summary.location
          ? `<div>Location: ${summary.location}</div>`
          : ""
      }

      <div>
        Evidence:
        ${summary.evidenceCount} sources
      </div>

      <div>
        Timeline:
        ${summary.timelineCount} events
      </div>

      <div>
        Impact:
        ${
          summary.impact?.status === "not_calculated"
            ? "Not calculated"
            : (summary.impact ? "Available" : "—")
        }
      </div>"""

if old not in text:
    raise SystemExit("Renderer block not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4F2 renderer fix applied")
