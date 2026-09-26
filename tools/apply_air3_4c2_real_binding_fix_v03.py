from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

# Insert impact section before source overview or before context if needed.
if "impact-summary-section" not in text:
    markers = [
        "    sourceOverviewSection,",
        "    contextSection,",
    ]

    insert = """
  const impactForecastSection = makeElement(
    'section',
    'detail-section impact-summary-section',
  );

  const impactVm = impactPayload
    ? impactSummaryViewModel(impactPayload)
    : null;

  impactForecastSection.innerHTML = `
    <div class="detail-section__title">
      Impact Forecast
    </div>
    <div class="detail-metrics">
      <div class="detail-metric">
        <div class="detail-metric__label">
          Targets
        </div>
        <div class="detail-metric__value">
          ${impactVm ? impactVm.targetCount : "—"}
        </div>
      </div>
    </div>
  `;

"""

    found = False
    for marker in markers:
        if marker in text:
            text = text.replace(marker, insert + marker, 1)
            found = True
            break

    if not found:
        raise SystemExit("Could not find insertion point")

if "impactForecastSection," not in text:
    text = text.replace(
        "    evidenceTimelineSection,",
        "    evidenceTimelineSection,\n    impactForecastSection,",
        1
    )

# Fix share summary empty payload
text = text.replace(
"""        evidence: [],
        timeline: [],
        impact: impactPayload,""",
"""        location: event.location || event.name || "Unknown",
        evidence: evidenceList?.children
          ? Array.from(evidenceList.children)
          : [],
        timeline: [],
        impact: impactPayload,""",
1
)

path.write_text(text, encoding="utf-8")
print("AIR-3.4C2 v03 patch applied")
