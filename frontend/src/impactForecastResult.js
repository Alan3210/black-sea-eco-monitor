import { t } from './i18n.js';

export function buildImpactForecastViewModel(payload = {}) {
  return {
    horizon: payload.horizon || [],
    affectedAreas: payload.affectedAreas ?? 0,
    closestDistanceKm: payload.closestDistanceKm ?? null,
    firstExposureHours: payload.firstExposureHours ?? null,
    status: payload.status || "ready",
  };
}

export function renderImpactForecastSummary(vm = {}, currentLanguage = 'ru') {
  return `
    <section class="detail-section impact-forecast-summary">
      <div class="detail-section__title">
        ${t(currentLanguage, 'impact.title')}
      </div>

      <div class="detail-metrics">
        <div class="detail-metric">
          <div class="detail-metric__label">
            ${t(currentLanguage, 'impact.affectedAreas')}
          </div>
          <div class="detail-metric__value">
            ${vm.affectedAreas}
          </div>
        </div>

        <div class="detail-metric">
          <div class="detail-metric__label">
            ${t(currentLanguage, 'impact.closestDistance')}
          </div>
          <div class="detail-metric__value">
            ${vm.closestDistanceKm ?? "—"} km
          </div>
        </div>
      </div>
    </section>
  `;
}
