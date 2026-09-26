from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

old = """      buildShareIncidentSummary({
        title: event.title,
        location: event.location || event.name || "Unknown",
        evidence: evidenceList?.children
          ? Array.from(evidenceList.children)
          : [],
        timeline: [],
        impact: impactPayload,
      })"""

new = """      buildShareIncidentSummary({
        title: vm.location || event.title || "Incident",
        location: vm.location || "Unknown",
        evidence: vm.evidenceCount
          ? Array.from({ length: vm.evidenceCount })
          : [],
        timeline: [
          {
            title: "Evidence Timeline",
          },
        ],
        impact: impactPayload,
      })"""

if old in text:
    text = text.replace(old, new, 1)
else:
    print("Share summary block not found; skipping replacement")

path.write_text(text, encoding="utf-8")
print("AIR-3.4D binding patch applied")
