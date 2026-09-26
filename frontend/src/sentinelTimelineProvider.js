import {
  createTimelinePoint,
  createTimelineSeries,
} from "./timelineDataContract.js";

export function normalizeSentinelTimelinePoints(
  points = [],
) {
  return points
    .filter((point) =>
      point &&
      point.timestamp &&
      Number.isFinite(point.value)
    )
    .map((point) =>
      createTimelinePoint(
        point.timestamp,
        point.value,
      )
    );
}

export function buildSentinelTimelineSeries(
  points = [],
) {
  return createTimelineSeries(
    "Sentinel-5P",
    normalizeSentinelTimelinePoints(points),
  );
}

export async function fetchSentinelTimeline(
  pollutant = "NO2",
  fetchImpl = fetch,
) {
  const response = await fetchImpl(
    `/air/timeline/sentinel5p?pollutant=${encodeURIComponent(pollutant)}`,
  );

  if (!response.ok) {
    throw new Error(
      `Sentinel-5P timeline request failed: ${response.status}`,
    );
  }

  const payload = await response.json();

  return buildSentinelTimelineSeries(
    payload.points || [],
  );
}
