from pathlib import Path

path = Path("frontend/src/i18n.js")
text = path.read_text(encoding="utf-8")

ru = """
    'impact.potential': 'Потенциальное воздействие',
    'impact.affectedAreas': 'Затронутые области',
    'impact.closestDistance': 'Ближайшее расстояние',
    'impact.firstExposure': 'Первое воздействие',
"""

en = """
    'impact.potential': 'Potential impact',
    'impact.affectedAreas': 'Affected areas',
    'impact.closestDistance': 'Closest distance',
    'impact.firstExposure': 'First exposure',
"""

# Insert into ru block if missing
if "'impact.potential':" not in text:
    marker = "    'impact.targets': 'Цели',"
    if marker in text:
        text = text.replace(marker, marker + "\n" + ru, 1)

# Insert into en block if missing
if text.count("'impact.potential':") < 2:
    marker = "    'impact.targets': 'Targets',"
    if marker in text:
        text = text.replace(marker, marker + "\n" + en, 1)

path.write_text(text, encoding="utf-8")

print("AIR-3.4G15 impact localization keys applied")
