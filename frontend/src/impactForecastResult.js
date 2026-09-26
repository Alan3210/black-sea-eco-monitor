export function buildImpactForecastViewModel(payload = {}) {
  return {
    horizon: payload.horizon || [],
    affectedAreas: payload.affectedAreas ?? 0,
    closestDistanceKm: payload.closestDistanceKm ?? null,
    firstExposureHours: payload.firstExposureHours ?? null,
    status: payload.status || "ready",
  };
}

export function renderImpactForecastSummary(vm = {}) {
  return `
    <section class="detail-section impact-forecast-summary">
      <div class="detail-section__title">
        Impact Forecast
      </div>

      <div class="detail-metrics">
        <div class="detail-metric">
          <div class="detail-metric__label">
            Affected areas
          </div>
          <div class="detail-metric__value">
            ${vm.affectedAreas}
          </div>
        </div>

        <div class="detail-metric">
          <div class="detail-metric__label">
            Closest distance
          </div>
          <div class="detail-metric__value">
            ${vm.closestDistanceKm ?? "—"} km
          </div>
        </div>
      </div>
    </section>
  `;
}
