export function buildIncidentReport(data = {}) {
  return {
    title: data.title || "Incident Report",
    location: data.location || "Unknown",
    time: data.time || "—",
    evidence: data.evidence || [],
    timeline: data.timeline || [],
    impact: data.impact || null,
  };
}

export function renderIncidentReportPreview(report = {}) {
  return `
    <section class="incident-report-preview">
      <h2>Incident Report</h2>\n      <h3>${report.title}</h3>

      <div>
        Location: ${report.location}
      </div>

      <div>
        Time: ${report.time}
      </div>

      <div>
        Evidence: ${report.evidence.length}
      </div>

      <div>
        Timeline events: ${report.timeline.length}
      </div>
    </section>
  `;
}
