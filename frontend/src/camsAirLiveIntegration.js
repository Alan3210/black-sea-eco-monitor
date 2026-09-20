
export const CAMS_RUNTIME_CONFIG = {
  sourceId: "cams-air-quality",
  layerId: "cams-air-quality-heatmap",
  endpoint: "/air/field",
  defaultPollutant: "pm25",
};


export function buildCamsRequestParams({
  pollutant = "pm25",
  stride = 2,
} = {}) {
  return new URLSearchParams({
    pollutant,
    stride: String(stride),
  });
}
