import { t } from './i18n.js';

export function buildImpactSummaryState(payload = {}) {
  return {
    status: payload.status || "ready",
    affectedAreas: payload.affectedAreas ?? 0,
    closestDistanceKm: payload.closestDistanceKm ?? null,
    firstExposureHours: payload.firstExposureHours ?? null,
    horizon: payload.horizon || [],
  };
}

export function renderImpactSummaryUX(state = {}, currentLanguage = 'ru') {
  return `
    <section class="detail-section impact-summary-section">
      <div class="detail-section__title">
        ${t(currentLanguage, 'impact.title')}
      </div>

      <div class="detail-metrics">
        <div class="detail-metric">
          <div class="detail-metric__label">
            ${t(currentLanguage, 'impact.potential')}
          </div>
          <div class="detail-metric__value">
            ${state.affectedAreas} areas
          </div>
        </div>

        <div class="detail-metric">
          <div class="detail-metric__label">
            ${t(currentLanguage, 'impact.closestDistance')}
          </div>
          <div class="detail-metric__value">
            ${state.closestDistanceKm ?? "—"} km
          </div>
        </div>

        <div class="detail-metric">
          <div class="detail-metric__label">
            ${t(currentLanguage, 'impact.firstExposure')}
          </div>
          <div class="detail-metric__value">
            ${state.firstExposureHours ?? "—"} h
          </div>
        </div>
      </div>
    </section>
  `;
}
