from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class NewsSource:

    name: str

    url: str

    language: str

    region: str

    source_type: str = "rss"

    reliability: float = 0.5

    enabled: bool = True


def google_news_url(
    query: str,
    language: str = "ru",
    country: str = "RU",
) -> str:

    encoded_query = quote_plus(query)

    return (
        "https://news.google.com/rss/search"
        f"?q={encoded_query}"
        f"&hl={language}"
        f"&gl={country}"
        f"&ceid={country}:{language}"
    )


NEWS_SOURCES = [

    # ==================================================
    # OFFICIAL RUSSIAN SOURCES — DIRECT RSS
    # ==================================================

    NewsSource(
        name="МЧС Краснодарского края — оперативная информация",
        url=(
            "https://23.mchs.gov.ru/"
            "deyatelnost/press-centr/"
            "operativnaya-informaciya/rss"
        ),
        language="ru",
        region="Krasnodar Krai",
        source_type="official_rss",
        reliability=0.95,
    ),

    NewsSource(
        name="МЧС Краснодарского края — новости",
        url=(
            "https://23.mchs.gov.ru/"
            "deyatelnost/press-centr/"
            "novosti/rss"
        ),
        language="ru",
        region="Krasnodar Krai",
        source_type="official_rss",
        reliability=0.95,
    ),

    NewsSource(
        name="МЧС Республики Крым — оперативная информация",
        url=(
            "https://82.mchs.gov.ru/"
            "deyatelnost/press-centr/"
            "operativnaya-informaciya/rss"
        ),
        language="ru",
        region="Crimea",
        source_type="official_rss",
        reliability=0.95,
    ),

    NewsSource(
        name="МЧС Севастополя — оперативная информация",
        url=(
            "https://92.mchs.gov.ru/"
            "deyatelnost/press-centr/"
            "operativnaya-informaciya/rss"
        ),
        language="ru",
        region="Sevastopol",
        source_type="official_rss",
        reliability=0.95,
    ),

    # ==================================================
    # GOOGLE NEWS — RUSSIAN LANGUAGE
    # ==================================================

    NewsSource(
        name="Google RU — Черное море загрязнение",
        url=google_news_url(
            '"Черное море" загрязнение when:7d'
        ),
        language="ru",
        region="Black Sea",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — разлив нефти Черное море",
        url=google_news_url(
            '"Черное море" "разлив нефти" when:7d'
        ),
        language="ru",
        region="Black Sea",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — мазут Анапа",
        url=google_news_url(
            'мазут Анапа when:7d'
        ),
        language="ru",
        region="Anapa",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — Новороссийск",
        url=google_news_url(
            'Новороссийск загрязнение море when:7d'
        ),
        language="ru",
        region="Novorossiysk",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — Туапсе",
        url=google_news_url(
            'Туапсе разлив нефтепродукты when:7d'
        ),
        language="ru",
        region="Tuapse",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — Сочи",
        url=google_news_url(
            'Сочи загрязнение море when:7d'
        ),
        language="ru",
        region="Sochi",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — Крым",
        url=google_news_url(
            'Крым загрязнение море when:7d'
        ),
        language="ru",
        region="Crimea",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — Севастополь",
        url=google_news_url(
            'Севастополь загрязнение море when:7d'
        ),
        language="ru",
        region="Sevastopol",
        source_type="google_news",
    ),

    NewsSource(
        name="Google RU — пожары Краснодарский край",
        url=google_news_url(
            '"Краснодарский край" пожар when:7d'
        ),
        language="ru",
        region="Krasnodar Krai",
        source_type="google_news",
    ),

    # ==================================================
    # OFFICIAL SITES THROUGH GOOGLE NEWS
    # ==================================================

    NewsSource(
        name="Росприроднадзор — Black Sea search",
        url=google_news_url(
            'site:rpn.gov.ru '
            '"Черное море" загрязнение when:7d'
        ),
        language="ru",
        region="Black Sea",
        source_type="google_news",
        reliability=0.95,
    ),

    NewsSource(
        name="Анапа официальный сайт",
        url=google_news_url(
            'site:anapa-official.ru '
            '(загрязнение OR мазут OR пожар) when:7d'
        ),
        language="ru",
        region="Anapa",
        source_type="google_news",
        reliability=0.9,
    ),

    NewsSource(
        name="Туапсинский округ официальный сайт",
        url=google_news_url(
            'site:tuapseregion.ru '
            '(загрязнение OR разлив OR пожар) when:7d'
        ),
        language="ru",
        region="Tuapse",
        source_type="google_news",
        reliability=0.9,
    ),

    # ==================================================
    # ENGLISH LANGUAGE — INTERNATIONAL COVERAGE
    # ==================================================

    NewsSource(
        name="Google EN — Black Sea pollution",
        url=google_news_url(
            '"Black Sea" pollution when:7d',
            language="en",
            country="US",
        ),
        language="en",
        region="Black Sea",
        source_type="google_news",
    ),

    NewsSource(
        name="Google EN — Black Sea oil spill",
        url=google_news_url(
            '"Black Sea" "oil spill" when:7d',
            language="en",
            country="US",
        ),
        language="en",
        region="Black Sea",
        source_type="google_news",
    ),

    NewsSource(
        name="Google EN — Black Sea wildfire",
        url=google_news_url(
            '"Black Sea" wildfire when:7d',
            language="en",
            country="US",
        ),
        language="en",
        region="Black Sea",
        source_type="google_news",
    ),
]