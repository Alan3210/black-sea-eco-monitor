from pathlib import Path

ROOT = Path("frontend/src")

# 1. Add missing i18n keys
i18n = ROOT / "i18n.js"
text = i18n.read_text(encoding="utf-8")

ru_insert = """
    'panel.evidenceDashboard': 'Панель доказательств',
    'sources.observation': 'Наблюдение',
    'sources.forecast': 'Прогноз',
    'sources.prediction': 'Прогнозирование',
    'timeline.title': 'Хронология доказательств',
    'timeline.satelliteObservation': 'Наблюдение спутника',
    'timeline.camsForecast': 'Прогноз CAMS',
    'timeline.eventDetected': 'Событие обнаружено',
    'timeline.evidenceUpdate': 'Обновление доказательств',
"""

en_insert = """
    'panel.evidenceDashboard': 'Evidence Dashboard',
    'sources.observation': 'Observation',
    'sources.forecast': 'Forecast',
    'sources.prediction': 'Prediction',
    'timeline.title': 'Evidence Timeline',
    'timeline.satelliteObservation': 'Satellite observation',
    'timeline.camsForecast': 'CAMS forecast',
    'timeline.eventDetected': 'Event detected',
    'timeline.evidenceUpdate': 'Evidence update',
"""

# Insert only if keys are absent
if "'timeline.satelliteObservation'" not in text:
    text = text.replace("  en: {", ru_insert + "\n\n  en: {", 1)
    text = text.replace("  },\n};", en_insert + "\n  },\n};", 1)

i18n.write_text(text, encoding="utf-8")


# 2. Timeline model gets localization keys
timeline = ROOT / "evidenceTimelineVisual.js"
text = timeline.read_text(encoding="utf-8")

if "i18nKey" not in text:
    text = text.replace(
"""  observation: {
    icon: "🛰",
    className: "timeline-observation",
  },""",
"""  observation: {
    icon: "🛰",
    className: "timeline-observation",
    i18nKey: "timeline.satelliteObservation",
  },""")
    text = text.replace(
"""  model: {
    icon: "🌍",
    className: "timeline-model",
  },""",
"""  model: {
    icon: "🌍",
    className: "timeline-model",
    i18nKey: "timeline.camsForecast",
  },""")
    text = text.replace(
"""  detection: {
    icon: "🔥",
    className: "timeline-detection",
  },""",
"""  detection: {
    icon: "🔥",
    className: "timeline-detection",
    i18nKey: "timeline.eventDetected",
  },""")
    text = text.replace(
"""  confirmation: {
    icon: "📡",
    className: "timeline-confirmation",
  },""",
"""  confirmation: {
    icon: "📡",
    className: "timeline-confirmation",
    i18nKey: "timeline.evidenceUpdate",
  },""")
    text = text.replace(
"""      className: visual.className,
    };""",
"""      className: visual.className,
      i18nKey: visual.i18nKey,
    };""")

timeline.write_text(text, encoding="utf-8")

print("AIR-3.4G9 localization completion patch applied")
