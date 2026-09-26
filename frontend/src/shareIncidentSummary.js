export function buildShareIncidentSummary(report = {}) {
  return {
    title: report.title || "Incident",
    location: report.location || "Unknown",
    evidenceCount: (report.evidence || []).length,
    timelineCount: (report.timeline || []).length,
    impact: report.impact || null,
  };
}

export function renderShareSummary(summary = {}) {
  return `
    <section class="share-summary">
      <h2>Incident Summary</h2>
      <h3>${summary.title}</h3>

      <div>Location: ${summary.location}</div>
      <div>Evidence: ${summary.evidenceCount}</div>
      <div>Timeline: ${summary.timelineCount}</div>
      <div>
        Impact:
        ${summary.impact ? "Available" : "—"}
      </div>

      <button>
        Copy Summary
      </button>
    </section>
  `;
}
