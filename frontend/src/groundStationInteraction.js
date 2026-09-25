import { buildGroundStationPopupHTML } from "./groundStationPopup.js";

export const GROUND_STATION_LAYER_ID = "ground-station-points";

export function getGroundStationFeature(event, layerId = GROUND_STATION_LAYER_ID) {
  const features = event?.features || [];

  return features.find(
    (feature) => feature.layer?.id === layerId
  ) || null;
}

export function buildGroundStationPopupFromFeature(feature) {
  if (!feature) {
    return null;
  }

  return buildGroundStationPopupHTML(
    feature.properties || {}
  );
}

export function attachGroundStationPopup(map, popupFactory) {
  map.on("click", GROUND_STATION_LAYER_ID, (event) => {
    const feature = getGroundStationFeature(event);

    if (!feature) {
      return;
    }

    const html = buildGroundStationPopupFromFeature(feature);

    if (html && popupFactory) {
      popupFactory(html, event.lngLat);
    }
  });
}
