from pathlib import Path

path = Path("frontend/src/i18n.js")
text = path.read_text(encoding="utf-8")

marker = "  en: {"

if "'impact.title'" not in text:
    ru_block = """
    'impact.title': 'Прогноз воздействия',
    'impact.targets': 'Цели',
    'sources.title': 'Источники данных',
    'sources.satellite': 'Спутник',
    'sources.model': 'Модель',
    'sources.simulation': 'Симуляция',
"""
    text = text.replace(marker, ru_block + "\n" + marker, 1)

# add EN values before the final export if needed
if "'impact.title'" not in text.split("  en: {", 1)[-1]:
    en_marker = "  },\n};"
    en_block = """
    'impact.title': 'Impact Forecast',
    'impact.targets': 'Targets',
    'sources.title': 'Data Sources',
    'sources.satellite': 'Satellite',
    'sources.model': 'Model',
    'sources.simulation': 'Simulation',
"""
    text = text.replace(en_marker, en_block + "\n" + en_marker, 1)

path.write_text(text, encoding="utf-8")
print("AIR-3.4G5 localization keys added")
