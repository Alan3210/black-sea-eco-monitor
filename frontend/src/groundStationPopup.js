export function formatGroundStationObservation(station = {}) {
  return {
    title: station.station_name || station.name || "Ground station",
    rows: [
      { label: "Country", value: station.country || "Unknown" },
      { label: "Pollutant", value: station.pollutant || "Unknown" },
      { label: "Value", value: station.value != null ? `${station.value} ${station.unit || ""}`.trim() : "Unknown" },
      { label: "Observed", value: station.observed_at || "Unknown" },
      { label: "Source", value: station.source || "EEA" },
    ],
  };
}

export function buildGroundStationPopupHTML(station = {}) {
  const model = formatGroundStationObservation(station);
  return `<div class="station-popup"><h3>${model.title}</h3>${model.rows.map(r => `<div><b>${r.label}:</b> ${r.value}</div>`).join("")}</div>`;
}
