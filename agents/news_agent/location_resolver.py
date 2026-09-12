import re

LOCATION_ALIASES = {
    "Novorossiysk": ["новороссийск", "novorossiysk", "дюрсо", "dyurso", "шесхарис", "sheskharis"],
    "Utrish Reserve": ["утриш", "большой утриш", "болшой утриш", "bolshoy utrish", "utrish", "utrish nature reserve", "заповедник утриш"],
    "Gelendzhik": ["геленджик", "gelendzhik"],
    "Anapa": ["анапа", "anapa"],
    "Sochi": ["сочи", "sochi"],
    "Sevastopol": ["севастополь", "sevastopol"],
}

def normalize_location_name(location_name: str | None) -> str | None:
    if not location_name:
        return None

    value = re.sub(r"[^a-zа-яё0-9\s]+", " ", location_name.lower())
    value = re.sub(r"\s+", " ", value).strip()

    for canonical, aliases in LOCATION_ALIASES.items():
        for alias in aliases:
            if alias.lower() in value:
                return canonical

    return location_name
