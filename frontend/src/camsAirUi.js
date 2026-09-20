export function createAirToggleState(
  enabled = false,
  pollutant = "pm25"
) {
  return {
    enabled,
    pollutant,
  };
}


export function buildAirLegend(
  pollutant = "pm25"
) {
  return {
    title:
      `CAMS ${pollutant.toUpperCase()}`,
    units:
      "µg/m³",
    stops: [
      0,
      10,
      25,
      50,
      100,
    ],
  };
}


export function shouldActivateAirLayer(
  state
) {
  return Boolean(
    state?.enabled
  );
}
