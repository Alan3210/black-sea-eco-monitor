from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

old = """      buildShareIncidentSummary({
        title: vm.location || event.title || "Incident",
        location: vm.location || "Unknown",
        evidence: vm.evidenceCount
          ? Array.from({ length: vm.evidenceCount })
          : [],
        timeline: [
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
        ],
        impact: impactPayload,
      })"""

new = """      buildShareIncidentSummary({
        title: vm.location || event.title || "Incident",
        location: null,
        evidence: vm.evidenceCount
          ? Array.from({ length: vm.evidenceCount })
          : [],
        timeline: [
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
        ],
        impact: impactPayload || {
          status: "not_calculated",
        },
      })"""

if old in text:
    text = text.replace(old, new, 1)
else:
    print("Summary binding block not found")

path.write_text(text, encoding="utf-8")
print("AIR-3.4F UX polish patch applied")
