export function createReportPreviewState(report = {}) {
  return {
    opened: false,
    report,
  };
}

export function renderReportPreview(state = {}) {
  const report = state.report || {};

  return `
    <section class="report-preview">
      <header>
        <h2>Incident Report</h2>
        <h3>${report.title || "Untitled incident"}</h3>
      </header>

      <div>
        Evidence:
        ${(report.evidence || []).length}
      </div>

      <div>
        Timeline events:
        ${(report.timeline || []).length}
      </div>

      <div>
        Impact:
        ${report.impact ? "Available" : "—"}
      </div>
    </section>
  `;
}
