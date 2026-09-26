from pathlib import Path

path = Path("frontend/src/main.js")
text = path.read_text(encoding="utf-8")

# Add i18nKey to timeline objects created in main.js
replacements = [
    (
        "title: 'Satellite observation',",
        "title: 'Satellite observation',\n        i18nKey: 'timeline.satelliteObservation',",
    ),
    (
        'title: \"Satellite observation\",',
        'title: \"Satellite observation\",\n            i18nKey: \"timeline.satelliteObservation\",',
    ),
    (
        "title: 'CAMS forecast',",
        "title: 'CAMS forecast',\n        i18nKey: 'timeline.camsForecast',",
    ),
    (
        "title: 'Event detected',",
        "title: 'Event detected',\n        i18nKey: 'timeline.eventDetected',",
    ),
    (
        "title: 'Evidence update',",
        "title: 'Evidence update',\n        i18nKey: 'timeline.evidenceUpdate',",
    ),
]

for old, new in replacements:
    if old in text and "i18nKey" not in text[text.find(old):text.find(old)+200]:
        text = text.replace(old, new, 1)

# Add source keys in the source overview payload.
text = text.replace(
    "type: 'Satellite',",
    "type: 'Satellite',\n        typeKey: 'sources.satellite',",
    1
)
text = text.replace(
    "purpose: 'Observation',",
    "purpose: 'Observation',\n        purposeKey: 'sources.observation',",
    1
)
text = text.replace(
    "type: 'Model',",
    "type: 'Model',\n        typeKey: 'sources.model',",
    1
)
text = text.replace(
    "purpose: 'Forecast',",
    "purpose: 'Forecast',\n        purposeKey: 'sources.forecast',",
    1
)
text = text.replace(
    "type: 'Simulation',",
    "type: 'Simulation',\n        typeKey: 'sources.simulation',",
    1
)
text = text.replace(
    "purpose: 'Prediction',",
    "purpose: 'Prediction',\n        purposeKey: 'sources.prediction',",
    1
)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G11 source and timeline data localization applied")
