from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

# Add helper sections before final append if not already present
anchor = """  eventPanelContent.append(
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

replacement = """  const impactForecastSection = makeElement(
    'section',
    'detail-section impact-summary-section',
  );

  impactForecastSection.innerHTML = `
    <div class="detail-section__title">
      Impact Forecast
    </div>
    <div class="detail-metrics">
      <div class="detail-metric">
        <div class="detail-metric__label">
          Status
        </div>
        <div class="detail-metric__value">
          ${impactPayload ? 'Available' : '—'}
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
    sourceOverviewSection,
    evidenceSection,
    shareSummarySection,
    contextSection,
    workflowSection,
  );"""

if anchor in text:
    text = text.replace(anchor, replacement, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4C patch applied")
