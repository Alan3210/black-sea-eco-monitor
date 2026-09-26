import {
  createTimelinePoint,
  createTimelineSeries,
} from "./timelineDataContract.js";

export function normalizeCAMSTimelinePoints(
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

export function buildCAMSTimelineSeries(
  points = [],
) {
  return createTimelineSeries(
    "CAMS",
    normalizeCAMSTimelinePoints(points),
  );
}

export async function fetchCAMSTimeline(
  pollutant = "PM10",
  fetchImpl = fetch,
) {
  const response = await fetchImpl(
    `/air/timeline/cams?pollutant=${encodeURIComponent(pollutant)}`,
  );

  if (!response.ok) {
    throw new Error(
      `CAMS timeline request failed: ${response.status}`,
    );
  }

  const payload = await response.json();

  return buildCAMSTimelineSeries(
    payload.points || [],
  );
}
