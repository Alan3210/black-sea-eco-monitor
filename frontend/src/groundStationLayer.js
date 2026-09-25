import { airStationsToGeoJSON } from "./airQuality.js";

export const GROUND_STATION_LAYER_CONFIG = {
  sourceId: "ground-stations",
  layerId: "ground-station-points",
};

export function buildGroundStationGeoJSON(stations = []) {
  return airStationsToGeoJSON(stations);
}

export function groundStationLayerStyle() {
  return {
    type: "circle",
    source: GROUND_STATION_LAYER_CONFIG.sourceId,
    paint: {
      "circle-radius": 6,
      "circle-opacity": 0.85,
    },
  };
}
