export function createImpactZoneSelection(zone = {}) {
  return {
    id: zone.id || null,
    name: zone.name || "Impact zone",
    distanceKm: zone.distanceKm ?? null,
    exposureHours: zone.exposureHours ?? null,
    risk: zone.risk || "Potential",
  };
}

export function renderImpactZoneDetails(zone = {}) {
  return `
    <section class="detail-section impact-zone-details">
      <div class="detail-section__title">
        Impact Zone
      </div>

      <div class="detail-metrics">
        <div class="detail-metric">
          <div class="detail-metric__label">
            Area
          </div>
          <div class="detail-metric__value">
            ${zone.name}
          </div>
        </div>

        <div class="detail-metric">
          <div class="detail-metric__label">
            Distance
          </div>
          <div class="detail-metric__value">
            ${zone.distanceKm ?? "—"} km
          </div>
        </div>

        <div class="detail-metric">
          <div class="detail-metric__label">
            Exposure
          </div>
          <div class="detail-metric__value">
            ${zone.exposureHours ?? "—"} h
          </div>
        </div>
      </div>
    </section>
  `;
}
