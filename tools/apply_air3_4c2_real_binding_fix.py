from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

# Replace empty share summary payload
old = """      buildShareIncidentSummary({
        title: event.title,
        evidence: [],
        timeline: [],
        impact: impactPayload,
      })"""

new = """      buildShareIncidentSummary({
        title: event.title || "Incident",
        location: event.location || event.name || "Unknown",
        evidence: evidenceList?.children
          ? Array.from(evidenceList.children)
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

# Insert impact section before source overview if available
anchor = """  eventPanelContent.append(
    header,
    pills,
    metrics,
    locationQuality,
    timeline,
    evidenceTimelineSection,
    sourceOverviewSection,"""

replacement = """  const impactForecastSection = makeElement(
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
      <div class="detail-metric">
        <div class="detail-metric__label">
          Threshold
        </div>
        <div class="detail-metric__value">
          ${impactVm ? `${impactVm.thresholdKm} km` : "—"}
        </div>
      </div>
    </div>
  `;

  eventPanelContent.append(
    header,
    pills,
    metrics,
    locationQuality,
    timeline,
    evidenceTimelineSection,
    impactForecastSection,
    sourceOverviewSection,"""

if anchor not in text:
    raise SystemExit("append anchor not found")

text = text.replace(anchor, replacement, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4C2 patch applied")
