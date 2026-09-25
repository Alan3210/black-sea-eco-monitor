const DEFAULT_ENDPOINT = "/air/stations";

export async function fetchGroundStations(
  fetchImpl = fetch,
  endpoint = DEFAULT_ENDPOINT,
) {
  const response = await fetchImpl(endpoint);

  if (!response.ok) {
    throw new Error(`Ground stations request failed: ${response.status}`);
  }

  const payload = await response.json();

  return (payload.stations || []).map(normalizeGroundStation);
}

export function normalizeGroundStation(station) {
  return {
    id: station.station_id ?? station.id ?? null,
    name: station.station_name ?? station.name ?? null,
    lat: station.latitude ?? station.lat ?? null,
    lon: station.longitude ?? station.lon ?? null,
    pollutant: station.pollutant ?? null,
    value: station.value ?? null,
    unit: station.unit ?? null,
    observed_at: station.observed_at ?? null,
    source: station.provenance?.provider ?? station.source ?? "EEA",
  };
}
