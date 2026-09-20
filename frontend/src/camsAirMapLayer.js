export function buildCamsAirHeatmapGeoJSON(
  field = {}
) {
  const features = [];

  const latitudes =
    field.grid?.latitudes || [];
  const longitudes =
    field.grid?.longitudes || [];
  const values =
    field.grid?.values || [];

  latitudes.forEach((lat, y) => {
    longitudes.forEach((lon, x) => {
      const value = values?.[y]?.[x];

      if (value !== null && value !== undefined) {
        features.push({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [lon, lat],
          },
          properties: {
            value,
          },
        });
      }
    });
  });

  return {
    type: "FeatureCollection",
    features,
  };
}


export function camsAirHeatmapStyle() {
  return {
    type: "heatmap",
    source: "cams-air-quality",
  };
}
