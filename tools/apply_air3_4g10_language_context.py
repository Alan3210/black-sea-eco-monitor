from pathlib import Path

# 1. Pass language into source overview renderer call
main = Path("frontend/src/main.js")
text = main.read_text(encoding="utf-8")

old = """    ${renderSourceOverview([
      {
        name: 'Sentinel-5P',
        type: 'Satellite',
        purpose: 'Observation',
      },
      {
        name: 'CAMS',
        type: 'Model',
        purpose: 'Forecast',
      },
      {
        name: 'Drift Model',
        type: 'Simulation',
        purpose: 'Prediction',
      },
    ])}"""

new = """    ${renderSourceOverview([
      {
        name: 'Sentinel-5P',
        type: 'Satellite',
        purpose: 'Observation',
      },
      {
        name: 'CAMS',
        type: 'Model',
        purpose: 'Forecast',
      },
      {
        name: 'Drift Model',
        type: 'Simulation',
        purpose: 'Prediction',
      },
    ], currentLanguage)}"""

if old in text:
    text = text.replace(old, new, 1)

main.write_text(text, encoding="utf-8")


# 2. Pass language through timeline binding
timeline = Path("frontend/src/evidenceTimelineEventBinding.js")
text = timeline.read_text(encoding="utf-8")

text = text.replace(
"""export function renderEventTimelineForPanel(
  event = {},
) {
  return renderEvidenceTimeline(
    event.timeline || [],
  );
}""",
"""export function renderEventTimelineForPanel(
  event = {},
  currentLanguage = 'ru',
) {
  return renderEvidenceTimeline(
    event.timeline || [],
    currentLanguage,
  );
}"""
)

timeline.write_text(text, encoding="utf-8")

print("AIR-3.4G10 language context propagation applied")
