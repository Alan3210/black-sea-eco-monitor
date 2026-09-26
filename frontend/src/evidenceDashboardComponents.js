export function buildSourcesCard(data = {}) {
  const sources = data.sources || {};

  return {
    title: "Sources Status",
    items: [
      {
        name: "EEA Station",
        available: !!sources.station_measurements,
      },
      {
        name: "CAMS Forecast",
        available: !!sources.model_forecast,
      },
      {
        name: "Sentinel-5P",
        available: !!sources.satellite_observation,
      },
    ],
  };
}

export function buildQualityCard(data = {}) {
  return {
    title: "Quality Overview",
    fresh: data.fresh_records || 0,
    stale: data.stale_records || 0,
  };
}

export function buildTimelinePanel(data = {}) {
  return {
    title: "Evidence Timeline",
    pollutant: data.pollutant || "Unknown",
    series: data.series || [],
  };
}

export function buildCrosscheckPanel(data = {}) {
  return {
    title: "Evidence Crosscheck",
    sources: data.sources || [],
  };
}
