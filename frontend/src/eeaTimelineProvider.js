import {
  createTimelinePoint,
  createTimelineSeries,
} from "./timelineDataContract.js";

export function normalizeEEATimelinePoints(
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

export function buildEEATimelineSeries(
  points = [],
) {
  return createTimelineSeries(
    "EEA",
    normalizeEEATimelinePoints(points),
  );
}

export async function fetchEEATimeline(
  stationId,
  fetchImpl = fetch,
) {
  if (!stationId) {
    return buildEEATimelineSeries([]);
  }

  const response = await fetchImpl(
    `/air/timeline/eea?station_id=${encodeURIComponent(stationId)}`,
  );

  if (!response.ok) {
    throw new Error(
      `EEA timeline request failed: ${response.status}`,
    );
  }

  const payload = await response.json();

  return buildEEATimelineSeries(
    payload.points || [],
  );
}
