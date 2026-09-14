export const DEFAULT_COORDINATE_PRECISION = 5;

export function coordinateKey(
  event,
  precision = DEFAULT_COORDINATE_PRECISION,
) {
  const latitude = Number(event?.latitude);
  const longitude = Number(event?.longitude);

  if (
    !Number.isFinite(latitude)
    || !Number.isFinite(longitude)
  ) {
    return null;
  }

  return [
    latitude.toFixed(precision),
    longitude.toFixed(precision),
  ].join(':');
}

export function groupCoLocatedEvents(
  events,
  precision = DEFAULT_COORDINATE_PRECISION,
) {
  const groupsByKey = new Map();

  for (const event of events) {
    const key = coordinateKey(event, precision);

    if (!key) continue;

    let group = groupsByKey.get(key);

    if (!group) {
      group = {
        id: `point:${key}`,
        key,
        latitude: event.latitude,
        longitude: event.longitude,
        locationName: event.locationName || 'Unknown location',
        events: [],
      };

      groupsByKey.set(key, group);
    }

    group.events.push(event);
  }

  return [...groupsByKey.values()].map((group) => ({
    ...group,
    count: group.events.length,
    isGroup: group.events.length > 1,
    eventIds: group.events.map((event) => event.id),
  }));
}

export function findGroupForEvent(groups, eventId) {
  return groups.find(
    (group) => group.eventIds.includes(eventId),
  ) ?? null;
}
