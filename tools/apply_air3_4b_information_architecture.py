from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

old = """  eventPanelContent.append(
    header,
    pills,
    metrics,
    locationQuality,
    timeline,
    evidenceTimelineSection,
    sourceOverviewSection,
    contextSection,
    workflowSection,
    evidenceSection,
    shareSummarySection,
  );"""

new = """  eventPanelContent.append(
    header,
    pills,
    metrics,
    locationQuality,

    timeline,
    evidenceTimelineSection,

    sourceOverviewSection,

    evidenceSection,

    shareSummarySection,

    contextSection,
    workflowSection,
  );"""

if old not in text:
    raise SystemExit("AIR-3.4B append block not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4B information architecture patch applied")
