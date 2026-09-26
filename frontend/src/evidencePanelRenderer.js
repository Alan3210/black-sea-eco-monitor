export function renderSourceList(sources = []) {
  return `
    <section class="evidence-panel-card">
      <h3>Sources</h3>
      <ul>
        ${sources.map((source) => `
          <li>
            ${source.available ? "🟢" : "🔴"}
            ${source.name || "Unknown"}
          </li>
        `).join("")}
      </ul>
    </section>
  `;
}

export function renderQualityBlock(quality = {}) {
  return `
    <section class="evidence-panel-card">
      <h3>Quality</h3>
      <div>Freshness: ${quality.freshness ?? "—"}</div>
      <div>Agreement: ${quality.agreement ?? "—"}</div>
    </section>
  `;
}

export function renderTimelineBlock(timeline = {}) {
  return `
    <section class="evidence-panel-card">
      <h3>Timeline</h3>
      <div>Pollutant: ${timeline.pollutant || "—"}</div>
    </section>
  `;
}

export function renderCrosscheckBlock(crosscheck = {}) {
  return `
    <section class="evidence-panel-card">
      <h3>Crosscheck</h3>
      <div>${crosscheck.status || "No data"}</div>
    </section>
  `;
}

export function renderEvidencePanel(payload = {}) {
  return `
    ${renderSourceList(payload.sources || [])}
    ${renderQualityBlock(payload.quality || {})}
    ${renderTimelineBlock(payload.timeline || {})}
    ${renderCrosscheckBlock(payload.crosscheck || {})}
  `;
}
