export function renderEvidenceDashboardHTML(
  model = {},
) {
  return `
    <div class="evidence-dashboard">
      <h2>${model.title || "Evidence Dashboard"}</h2>

      <section class="dashboard-summary">
        <h3>Sources Status</h3>
        <pre>${JSON.stringify(
          model.summary || {},
          null,
          2,
        )}</pre>
      </section>

      <section class="dashboard-timeline">
        <h3>Timeline</h3>
        <pre>${JSON.stringify(
          model.timeline || {},
          null,
          2,
        )}</pre>
      </section>

      <section class="dashboard-quality">
        <h3>Quality Overview</h3>
        <pre>${JSON.stringify(
          model.quality || {},
          null,
          2,
        )}</pre>
      </section>
    </div>
  `;
}
