from pathlib import Path

files = {
    "frontend/src/evidenceDashboardComponents.js": [
        ("Evidence Dashboard", "${t(currentLanguage, 'panel.evidenceDashboard')}"),
    ],
    "frontend/src/evidenceTimelineRenderer.js": [
        ("Evidence Timeline", "${t(currentLanguage, 'timeline.title')}"),
        ("Satellite observation", "${t(currentLanguage, 'timeline.satelliteObservation')}"),
        ("CAMS forecast", "${t(currentLanguage, 'timeline.camsForecast')}"),
        ("Event detected", "${t(currentLanguage, 'timeline.eventDetected')}"),
        ("Evidence update", "${t(currentLanguage, 'timeline.evidenceUpdate')}"),
    ],
    "frontend/src/sourceOverviewBlock.js": [
        ("Data Sources", "${t(currentLanguage, 'sources.title')}"),
        ("Satellite", "${t(currentLanguage, 'sources.satellite')}"),
        ("Model", "${t(currentLanguage, 'sources.model')}"),
        ("Simulation", "${t(currentLanguage, 'sources.simulation')}"),
        ("Observation", "${t(currentLanguage, 'sources.observation')}"),
        ("Forecast", "${t(currentLanguage, 'sources.forecast')}"),
        ("Prediction", "${t(currentLanguage, 'sources.prediction')}"),
    ],
}

for filename, replacements in files.items():
    path = Path(filename)
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")

    for old, new in replacements:
        text = text.replace(old, new, 1)

    path.write_text(text, encoding="utf-8")

print("AIR-3.4G7 localization pass applied")
