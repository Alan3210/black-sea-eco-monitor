from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

# imports
anchor = "import {\n  DEFAULT_IMPACT_THRESHOLD_KM,"
imports = """import {
  renderSourceOverview,
} from './sourceOverviewBlock.js';

import {
  buildShareIncidentSummary,
  renderShareSummary,
} from './shareIncidentSummary.js';

"""
if "renderSourceOverview" not in text:
    text = text.replace(anchor, imports + anchor, 1)

# sections before append
anchor = """  eventPanelContent.append(
    header,
    pills,
    metrics,
    locationQuality,
    timeline,
    evidenceTimelineSection,
    contextSection,
    workflowSection,
    evidenceSection,
  );"""

replacement = """  const sourceOverviewSection = makeElement(
    'section',
    'detail-section source-overview-section',
  );

  sourceOverviewSection.innerHTML = `
    <div class="detail-section__title">
      Data Sources
    </div>
    ${renderSourceOverview([
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
    ])}
  `;

  const shareSummarySection = makeElement(
    'section',
    'detail-section share-summary-section',
  );

  shareSummarySection.innerHTML =
    renderShareSummary(
      buildShareIncidentSummary({
        title: event.title,
        evidence: [],
        timeline: [],
        impact: impactPayload,
      }),
    );

  eventPanelContent.append(
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

if anchor not in text:
    raise SystemExit("append anchor not found")

text = text.replace(anchor, replacement, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4A patch applied")
