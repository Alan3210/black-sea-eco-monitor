export const DEFAULT_STATION_POLLUTANTS = Object.freeze([
  "PM10",
  "PM2.5",
  "NO2",
  "SO2",
  "O3",
]);

export const DEFAULT_STATION_SOURCES = Object.freeze([
  "EEA",
]);

export function stationReferenceTime(station) {
  const candidates = [
    station?.observed_at,
    station?.updated_at,
    station?.timestamp,
  ];

  for (const value of candidates) {
    if (!value) continue;
    const time = Date.parse(value);
    if (Number.isFinite(time)) return time;
  }

  return null;
}

export function filterGroundStations(
  stations = [],
  {
    pollutants = DEFAULT_STATION_POLLUTANTS,
    sources = DEFAULT_STATION_SOURCES,
    days = 7,
    now = Date.now(),
  } = {},
) {
  const pollutantSet = new Set(pollutants);
  const sourceSet = new Set(sources);

  const cutoff = days === "all"
    ? null
    : now - Number(days) * 86_400_000;

  return stations.filter((station) => {
    if (!pollutantSet.has(station.pollutant)) return false;
    if (!sourceSet.has(station.source)) return false;

    if (cutoff === null) return true;

    const referenceTime = stationReferenceTime(station);

    if (referenceTime === null) return true;

    return referenceTime >= cutoff;
  });
}
