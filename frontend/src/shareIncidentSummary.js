export function buildShareIncidentSummary(report = {}) {
  return {
    title: report.title || "Incident",
    location: report.location || null,
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

      ${
        summary.location
          ? `<div>Location: ${summary.location}</div>`
          : ""
      }

      <div>
        Evidence:
        ${summary.evidenceCount} sources
      </div>

      <div>
        Timeline:
        ${summary.timelineCount} events
      </div>

      <div>
        Impact:
        ${
          summary.impact?.status === "not_calculated"
            ? "Not calculated"
            : (summary.impact ? "Available" : "—")
        }
      </div>

      <button>
        Copy Summary
      </button>
    </section>
  `;
}
