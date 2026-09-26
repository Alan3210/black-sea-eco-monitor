import { t } from './i18n.js';

export function buildShareIncidentSummary(report = {}) {
  return {
    title: report.title || "Incident",
    location: report.location || null,
    evidenceCount: (report.evidence || []).length,
    timelineCount: (report.timeline || []).length,
    impact: report.impact || null,
  };
}

export function renderShareSummary(summary = {}, currentLanguage = null) {
  const label = (key, fallback) =>
    currentLanguage
      ? t(currentLanguage, key)
      : fallback;

  return `
    <section class="share-summary">
      <h2>${label('incidentSummary.title', 'Incident Summary')}</h2>
      <h3>${summary.title}</h3>

      ${
        summary.location
          ? `<div>Location: ${summary.location}</div>`
          : ""
      }

      <div>
        ${label('incidentSummary.evidence', 'Evidence')}:
        ${summary.evidenceCount} sources
      </div>

      <div>
        ${label('incidentSummary.timeline', 'Timeline')}:
        ${summary.timelineCount} events
      </div>

      <div>
        ${label('incidentSummary.impact', 'Impact')}:
        ${
          summary.impact?.status === "not_calculated"
            ? label('incidentSummary.notCalculated', 'Not calculated')
            : (summary.impact ? "Available" : "—")
        }
      </div>

      <button>
        Copy Summary
      </button>
    </section>
  `;
}
