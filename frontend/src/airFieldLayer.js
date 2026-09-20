export const AIR_POLLUTANTS = {
  pm25: {
    label: "PM2.5",
    units: "µg/m³",
  },
  pm10: {
    label: "PM10",
    units: "µg/m³",
  },
  no2: {
    label: "NO₂",
    units: "µg/m³",
  },
  so2: {
    label: "SO₂",
    units: "µg/m³",
  },
  o3: {
    label: "O₃",
    units: "µg/m³",
  },
  dust: {
    label: "Dust",
    units: "µg/m³",
  },
};


export function normalizeAirFieldPayload(
  payload = {}
) {
  return {
    provider:
      payload.provider ||
      "CAMS",
    pollutant:
      payload.pollutant?.id ||
      "pm25",
    units:
      payload.pollutant?.units ||
      "µg/m³",
    grid:
      payload.grid || {
        latitudes: [],
        longitudes: [],
        values: [],
      },
    validTime:
      payload.valid_time ||
      null,
    semantics:
      payload.semantics || {
        kind: "model_forecast",
      },
  };
}


export function airFieldToHeatmapPoints(
  payload
) {
  const field =
    normalizeAirFieldPayload(
      payload
    );

  const points = [];

  field.grid.latitudes.forEach(
    (lat, y) => {
      field.grid.longitudes.forEach(
        (lon, x) => {
          const value =
            field.grid.values?.[y]?.[x];

          if (value !== null &&
              value !== undefined) {
            points.push({
              lon,
              lat,
              value,
            });
          }
        }
      );
    }
  );

  return points;
}


export function airLegendStops(
  pollutant = "pm25"
) {
  return {
    pollutant,
    stops: [
      0,
      10,
      25,
      50,
      100,
    ],
    units:
      AIR_POLLUTANTS[pollutant]?.units ||
      "µg/m³",
  };
}
