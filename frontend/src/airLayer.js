import {
  airQualityColor,
  airStationsToGeoJSON,
} from "./airQuality.js";


export function createAirStationSourceData(
  payload = {}
) {
  return airStationsToGeoJSON(
    payload.stations || []
  );
}


export function airStationCircleStyle(
  feature
) {
  return {
    color:
      airQualityColor(
        feature?.properties?.status
      ),
    radius: 7,
    strokeColor: "#ffffff",
    strokeWidth: 1.5,
  };
}


export function buildAirPopupData(
  properties = {}
) {
  return {
    title:
      properties.name
      || "Air station",
    pm25:
      properties.pm25 ?? null,
    pm10:
      properties.pm10 ?? null,
    no2:
      properties.no2 ?? null,
    so2:
      properties.so2 ?? null,
    o3:
      properties.o3 ?? null,
    co:
      properties.co ?? null,
    source:
      properties.source
      || "Ground observation",
    observedAt:
      properties.observed_at
      || null,
    status:
      properties.status
      || "unknown",
  };
}
