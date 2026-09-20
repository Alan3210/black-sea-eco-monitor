export function createAtmospherePanelState() {
  return {
    windEnabled: true,
    airEnabled: false,
    pollutant: "pm25",
  };
}

export function toggleAirLayer(state, enabled) {
  return {
    ...state,
    airEnabled: Boolean(enabled),
  };
}

export function setAirPollutant(state, pollutant) {
  return {
    ...state,
    pollutant,
  };
}

export function shouldShowAirLegend(state) {
  return Boolean(state?.airEnabled);
}
