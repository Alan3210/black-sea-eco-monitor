from agents.news_agent.models import NewsItem


ENVIRONMENTAL_KEYWORDS = [
    "pollution",
    "oil spill",
    "oil pollution",
    "wildfire",
    "forest fire",
    "chemical spill",
    "contamination",
    "sewage",
    "algae bloom",
    "fish mortality",
    "dead fish",

    "загрязнение",
    "разлив нефти",
    "мазут",
    "нефтепродукты",
    "пожар",
    "лесной пожар",
    "химический выброс",
    "сточные воды",
    "цветение воды",
    "гибель рыбы",
]


def filter_environmental_news(
    items: list[NewsItem]
) -> list[NewsItem]:

    filtered = []

    for item in items:

        text = (
            f"{item.title} "
            f"{item.summary or ''}"
        ).lower()

        if any(
            keyword in text
            for keyword in ENVIRONMENTAL_KEYWORDS
        ):
            filtered.append(item)

    return filtered