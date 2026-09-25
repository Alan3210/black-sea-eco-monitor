export const GROUND_STATION_POLLUTANT_LABELS = Object.freeze({
  "PM10": "PM10",
  "PM2.5": "PM2.5",
  "NO2": "NO₂",
  "SO2": "SO₂",
  "O3": "O₃",
});

export function formatGroundStationLegendEntry(
  station = {},
) {
  const pollutant = station.pollutant || "Unknown";

  return {
    pollutant,
    label:
      GROUND_STATION_POLLUTANT_LABELS[pollutant] ||
      pollutant,
    unit: station.unit || "",
    source: station.source || "EEA",
    semantics: "station_measurement",
  };
}

export function buildGroundStationLegend(
  stations = [],
) {
  const entries = new Map();

  stations.forEach((station) => {
    const entry = formatGroundStationLegendEntry(station);
    entries.set(
      `${entry.pollutant}:${entry.unit}`,
      entry,
    );
  });

  return [...entries.values()];
}
