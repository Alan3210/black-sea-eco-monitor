export async function fetchMonitorEventContext(
  eventId,
  fetchImpl = fetch,
) {
  const response = await fetchImpl(
    `/monitor/events/${encodeURIComponent(eventId)}/context`,
    {
      headers: { Accept: 'application/json' },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Monitor context API returned HTTP ${response.status}`,
    );
  }

  return response.json();
}

export function monitorContextViewModel(context) {
  const capabilities = context?.capabilities ?? {};
  const readiness = context?.readiness ?? {};

  return {
    satelliteCount: Number.isFinite(
      Number(context?.satellite?.count),
    )
      ? Number(context.satellite.count)
      : 0,
    hasCoordinates: Boolean(
      readiness.event_has_coordinates,
    ),
    driftReady: Boolean(
      capabilities.ocean_drift?.available,
    ),
    impactReady: Boolean(
      capabilities.impact_screening?.available,
    ),
    arReady: Boolean(
      capabilities.ar_scene?.available,
    ),
  };
}
