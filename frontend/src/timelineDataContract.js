export const TIMELINE_SOURCES = [
  "EEA",
  "CAMS",
  "Sentinel-5P",
];

export function createTimelinePoint(
  timestamp,
  value,
) {
  return {
    timestamp,
    value,
  };
}

export function createTimelineSeries(
  source,
  points = [],
) {
  return {
    source,
    points,
  };
}

export function normalizeTimelinePayload(
  payload = {},
) {
  return {
    pollutant: payload.pollutant || "PM10",
    series: TIMELINE_SOURCES.map((source) => {
      const found = (payload.series || [])
        .find((item) => item.source === source);

      return createTimelineSeries(
        source,
        found?.points || [],
      );
    }),
  };
}
