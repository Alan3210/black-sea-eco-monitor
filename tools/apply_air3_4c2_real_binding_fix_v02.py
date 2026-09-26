
from pathlib import Path
import re

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

# Fix Share Summary payload if present
text = text.replace(
"""        evidence: [],
        timeline: [],
        impact: impactPayload,""",
"""        location: event.location || event.name || "Unknown",
        evidence: evidenceList?.children
          ? Array.from(evidenceList.children)
          : [],
        timeline: [
          {
            title: "Evidence Timeline",
          },
        ],
        impact: impactPayload,""",
1
)

# Insert impact section before source overview using regex
if "impact-summary-section" not in text:
    pattern = re.compile(
        r"(\\s+eventPanelContent\\.append\\(\\s*\\n"
        r"\\s+header,\\s*\\n"
        r"\\s+pills,\\s*\\n"
        r"\\s+metrics,\\s*\\n"
        r"\\s+locationQuality,\\s*\\n"
        r"\\s+timeline,\\s*\\n"
        r"\\s+evidenceTimelineSection,\\s*\\n)",
        re.MULTILINE,
    )

    replacement = r"""\1
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

    text, count = pattern.subn(replacement, text, count=1)
    if count == 0:
        raise SystemExit("Could not find eventPanelContent insertion point")

# Add section to append if missing
text = text.replace(
"    evidenceTimelineSection,\n    sourceOverviewSection,",
"    evidenceTimelineSection,\n    impactForecastSection,\n    sourceOverviewSection,",
1
)

path.write_text(text, encoding="utf-8")
print("AIR-3.4C2 v02 patch applied")
