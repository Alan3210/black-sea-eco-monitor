const SOURCE_STYLES = Object.freeze({
  station_measurement: {
    icon: "🟢",
    label: "Ground Station",
    cssClass: "evidence-source-station",
  },

  model_forecast: {
    icon: "🔵",
    label: "Model Forecast",
    cssClass: "evidence-source-model",
  },

  satellite_observation: {
    icon: "🛰",
    label: "Satellite Observation",
    cssClass: "evidence-source-satellite",
  },
});

export function getEvidenceSourceStyle(
  sourceType = "unknown",
) {
  return (
    SOURCE_STYLES[sourceType] || {
      icon: "⚪",
      label: "Unknown Source",
      cssClass: "evidence-source-unknown",
    }
  );
}

export function decorateEvidenceSections(
  sections = [],
) {
  return sections.map((section) => ({
    ...section,
    style: getEvidenceSourceStyle(section.type),
  }));
}
