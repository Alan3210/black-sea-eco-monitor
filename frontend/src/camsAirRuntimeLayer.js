import {
  buildCamsAirHeatmapGeoJSON,
} from "./camsAirMapLayer.js";


export async function fetchCamsAirField(
  {
    pollutant = "pm25",
    runDate = null,
    leadHour = null,
    stride = 2,
  } = {}
) {
  const params =
    new URLSearchParams({
      pollutant,
      stride: String(stride),
    });

  if (runDate) {
    params.set(
      "run_date",
      runDate
    );
  }

  if (leadHour !== null) {
    params.set(
      "lead_hour",
      String(leadHour)
    );
  }

  const response =
    await fetch(
      `/air/field?${params.toString()}`
    );

  if (!response.ok) {
    throw new Error(
      `CAMS air field request failed: ${response.status}`
    );
  }

  return response.json();
}


export function createCamsAirRuntimeLayer(
  fieldPayload
) {
  return {
    source:
      "cams-air-quality",
    geojson:
      buildCamsAirHeatmapGeoJSON(
        fieldPayload
      ),
    layer: {
      id:
        "cams-air-quality-heatmap",
      type:
        "heatmap",
      source:
        "cams-air-quality",
    },
  };
}
