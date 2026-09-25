const TIMELINE_SOURCE_STYLES = Object.freeze({
  station_measurement: {
    icon: "🟢",
    label: "Ground Station",
    cssClass: "timeline-source-station",
  },

  model_forecast: {
    icon: "🔵",
    label: "Model Forecast",
    cssClass: "timeline-source-model",
  },

  satellite_observation: {
    icon: "🛰",
    label: "Satellite Observation",
    cssClass: "timeline-source-satellite",
  },
});

export function getTimelineSourceStyle(
  sourceType = "unknown",
) {
  return (
    TIMELINE_SOURCE_STYLES[sourceType] || {
      icon: "⚪",
      label: "Unknown Source",
      cssClass: "timeline-source-unknown",
    }
  );
}

export function decorateTimelineSeries(series = []) {
  return series.map((item) => ({
    ...item,
    style: getTimelineSourceStyle(item.type),
  }));
}
