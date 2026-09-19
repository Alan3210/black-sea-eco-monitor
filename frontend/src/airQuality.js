export function normalizeAirStatus(status) {
  if (
    ["good", "moderate", "poor"].includes(status)
  ) {
    return status;
  }

  return "unknown";
}


export function airQualityColor(status) {
  const normalized =
    normalizeAirStatus(status);

  const colors = {
    good: "#3ddc97",
    moderate: "#f5c542",
    poor: "#ff6b6b",
    unknown: "#9ca3af",
  };

  return colors[normalized];
}


export function airStationToFeature(station) {
  return {
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [
        station.lon,
        station.lat,
      ],
    },
    properties: {
      id: station.id,
      name: station.name,
      status:
        normalizeAirStatus(
          station.status
        ),
      pm25: station.pm25 ?? null,
      pm10: station.pm10 ?? null,
      no2: station.no2 ?? null,
      so2: station.so2 ?? null,
      o3: station.o3 ?? null,
      co: station.co ?? null,
      source:
        station.source
        || "Ground observation",
      observed_at:
        station.observed_at
        || station.updated_at
        || null,
    },
  };
}


export function airStationsToGeoJSON(
  stations = []
) {
  return {
    type: "FeatureCollection",
    features:
      stations.map(
        airStationToFeature
      ),
  };
}
