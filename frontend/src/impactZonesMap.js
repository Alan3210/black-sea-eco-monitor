export function buildImpactZonesState(payload = {}) {
  return {
    available: Array.isArray(payload?.zones)
      && payload.zones.length > 0,
    zones: payload?.zones || [],
  };
}

export function impactZonesToFeatures(state = {}) {
  if (!state.available) {
    return {
      type: "FeatureCollection",
      features: [],
    };
  }

  return {
    type: "FeatureCollection",
    features: state.zones.map((zone) => ({
      type: "Feature",
      geometry: zone.geometry || null,
      properties: {
        name: zone.name || "Impact zone",
        exposureHours: zone.exposureHours ?? null,
      },
    })),
  };
}
