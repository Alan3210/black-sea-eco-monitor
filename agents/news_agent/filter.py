from agents.news_agent.models import NewsItem


ENVIRONMENTAL_KEYWORDS = [

    # English
    "pollution",
    "oil spill",
    "oil pollution",
    "wildfire",
    "forest fire",
    "chemical spill",
    "chemical release",
    "contamination",
    "sewage",
    "algae bloom",
    "fish mortality",
    "dead fish",
    "contaminated runoff",

    # Russian
    "загрязнение",
    "загрязнен",
    "разлив",
    "разлив нефти",
    "мазут",
    "нефтепродукт",
    "пожар",
    "лесопожар",
    "пожароопас",
    "химический выброс",
    "выброс",
    "сточные воды",
    "стоки",
    "цветение воды",
    "гибель рыбы",
    "мор рыбы",
]


BLACK_SEA_REGION_KEYWORDS = [

    # General
    "black sea",
    "черное море",
    "чёрное море",
    "черноморск",
    "черноморский",

    # Russia
    "krasnodar krai",
    "краснодарский край",
    "кубань",

    "anapa",
    "анапа",
    "анапский",

    "novorossiysk",
    "новороссийск",

    "gelendzhik",
    "геленджик",

    "tuapse",
    "туапсе",
    "туапсин",

    "sochi",
    "сочи",

    "crimea",
    "крым",

    "sevastopol",
    "севастополь",

    "kerch",
    "керч",

    # Ukraine
    "odesa",
    "odessa",
    "одесса",
    "одеса",

    "kherson",
    "херсон",

    # Georgia
    "batumi",
    "батуми",

    # Turkey
    "trabzon",
    "трабзон",

    # Bulgaria
    "bulgaria",
    "болгария",
    "varna",
    "варна",
    "burgas",
    "бургас",

    # Romania
    "romania",
    "румыния",
    "constanta",
    "констанца",
]


INCIDENT_KEYWORDS = [

    # English
    "spill",
    "oil spill",
    "pollution",
    "contamination",
    "sewage",
    "chemical release",
    "wildfire",
    "forest fire",
    "dead fish",
    "fish mortality",
    "algae bloom",

    # Russian
    "разлив",
    "мазут",
    "нефтепродукт",
    "загрязнение",
    "загрязнен",
    "сточные воды",
    "выброс",
    "пожар",
    "лесопожар",
    "пожароопас",
    "гибель рыбы",
    "мор рыбы",
    "цветение воды",
]


def build_search_text(
    item: NewsItem
) -> str:

    return (
        f"{item.title} "
        f"{item.summary or ''}"
    ).lower()


def filter_environmental_news(
    items: list[NewsItem]
) -> list[NewsItem]:

    filtered = []

    for item in items:

        text = build_search_text(
            item
        )

        has_environmental_signal = any(
            keyword in text
            for keyword in ENVIRONMENTAL_KEYWORDS
        )

        if has_environmental_signal:

            filtered.append(
                item
            )

    return filtered


def filter_black_sea_incidents(
    items: list[NewsItem]
) -> list[NewsItem]:

    results = []

    for item in items:

        text = build_search_text(
            item
        )

        has_region = any(
            keyword in text
            for keyword in BLACK_SEA_REGION_KEYWORDS
        )

        has_incident = any(
            keyword in text
            for keyword in INCIDENT_KEYWORDS
        )

        if (
            has_region
            and has_incident
        ):

            results.append(
                item
            )

    return results