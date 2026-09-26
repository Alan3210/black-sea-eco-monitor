import {
  buildSourcesCard,
  buildQualityCard,
  buildTimelinePanel,
  buildCrosscheckPanel,
} from "./evidenceDashboardComponents.js";

function renderSources(card) {
  return `
    <div class="evidence-card evidence-card--sources">
      <h3>${card.title}</h3>
      <ul>
        ${card.items.map((item) => `
          <li>
            <span>${item.available ? "🟢" : "🔴"}</span>
            ${item.name}
          </li>
        `).join("")}
      </ul>
    </div>
  `;
}

function renderQuality(card) {
  return `
    <div class="evidence-card evidence-card--quality">
      <h3>${card.title}</h3>
      <div>Fresh: ${card.fresh}</div>
      <div>Stale: ${card.stale}</div>
    </div>
  `;
}

function renderTimeline(card) {
  return `
    <div class="evidence-card evidence-card--timeline">
      <h3>${card.title}</h3>
      <div>Pollutant: ${card.pollutant}</div>
    </div>
  `;
}

function renderCrosscheck(card) {
  return `
    <div class="evidence-card evidence-card--crosscheck">
      <h3>${card.title}</h3>
    </div>
  `;
}

export function renderDashboardComponents(data = {}) {
  const sources = buildSourcesCard(data.summary || {});
  const quality = buildQualityCard(
    data.summary?.quality || {},
  );
  const timeline = buildTimelinePanel(data.timeline || {});
  const crosscheck = buildCrosscheckPanel(data.crosscheck || {});

  return `
    <div class="evidence-dashboard-grid">
      ${renderSources(sources)}
      ${renderQuality(quality)}
      ${renderTimeline(timeline)}
      ${renderCrosscheck(crosscheck)}
    </div>
  `;
}

export function renderEvidenceDashboardHTML(
  model = {},
) {
  return `
    <div class="evidence-dashboard">
      <h2>Evidence Dashboard</h2>
      ${renderDashboardComponents(model)}
    </div>
  `;
}
