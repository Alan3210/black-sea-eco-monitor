from pathlib import Path

path = Path("frontend/src/i18n.js")

text = path.read_text(encoding="utf-8")

marker = "    'canonicalLocation.Crimea':"

insert = """
    'impact.title': 'Прогноз воздействия',
    'impact.targets': 'Цели',

    'sources.title': 'Источники данных',
    'sources.satellite': 'Спутник',
    'sources.model': 'Модель',
    'sources.simulation': 'Симуляция',
    'sources.observation': 'Наблюдение',
    'sources.forecast': 'Прогноз',
    'sources.prediction': 'Прогнозирование',

    'panel.evidenceDashboard': 'Панель доказательств',

    'timeline.title': 'Хронология доказательств',
    'timeline.satelliteObservation': 'Наблюдение спутника',
    'timeline.camsForecast': 'Прогноз CAMS',
    'timeline.eventDetected': 'Событие обнаружено',
    'timeline.evidenceUpdate': 'Обновление доказательств',
"""

if "'sources.satellite': 'Спутник'" not in text:
    pos = text.find(marker)

    if pos == -1:
        raise SystemExit("RU marker not found")

    end = text.find("\n", pos)

    text = (
        text[:end + 1]
        + insert
        + text[end + 1:]
    )

    path.write_text(text, encoding="utf-8")

print("RU i18n keys inserted")