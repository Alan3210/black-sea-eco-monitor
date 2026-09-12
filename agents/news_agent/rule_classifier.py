from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)

from backend.models.event import EventCategory
from agents.news_agent.models import NewsItem


def detect_category(text: str):

    text = text.lower()

    # --------------------------------------------------
    # Industrial fires
    # --------------------------------------------------

    fire_terms = [
        "fire",
        "пожар",
        "возгора",
        "горит",
        "горел",
    ]

    industrial_terms = [
        "terminal",
        "refinery",
        "industrial",
        "factory",
        "plant",
        "oil depot",
        "fuel depot",
        "tank farm",
        "port terminal",

        "терминал",
        "нефтебаз",
        "нпз",
        "нефтеперераб",
        "завод",
        "предприят",
        "промышлен",
        "порт",
        "резервуар",
        "хранилищ",
        "подстанц",
    ]

    has_fire = any(
        term in text
        for term in fire_terms
    )

    has_industrial_context = any(
        term in text
        for term in industrial_terms
    )

    if (
        has_fire
        and has_industrial_context
    ):
        return EventCategory.industrial_fire

    # --------------------------------------------------
    # Wildfires / vegetation fires
    # --------------------------------------------------

    wildfire_terms = [
        "wildfire",
        "forest fire",
        "vegetation fire",
        "brush fire",

        "лесной пожар",
        "лесных пожара",
        "лесных пожаров",
        "природный пожар",
        "ландшафтный пожар",
        "горит лес",
        "лес горит",
        "пожар в лесном массиве",
        "лесопожар",
        "заповедник",
    ]

    if any(
        term in text
        for term in wildfire_terms
    ):
        return EventCategory.wildfire

    # --------------------------------------------------
    # Edible / vegetable oil pollution
    # --------------------------------------------------

    edible_oil_terms = [
        "sunflower oil",
        "vegetable oil",
        "edible oil",
        "cooking oil",

        "подсолнечное масло",
        "растительное масло",
        "пищевое масло",
    ]

    if any(
        term in text
        for term in edible_oil_terms
    ):
        return EventCategory.water_pollution

    # --------------------------------------------------
    # Petroleum spills / pollution
    # --------------------------------------------------

    petroleum_terms = [
        "petroleum",
        "crude oil",
        "fuel oil",
        "diesel",
        "hydrocarbon",
        "mazut",

        "нефть",
        "мазут",
        "нефтепродукт",
        "дизель",
        "топливо",
    ]

    spill_terms = [
        "spill",
        "pollution",
        "contamination",
        "leak",
        "discharge",

        "разлив",
        "загрязнен",
        "загрязнение",
        "утечк",
        "сброс",
    ]

    has_petroleum = any(
        term in text
        for term in petroleum_terms
    )

    has_spill_signal = any(
        term in text
        for term in spill_terms
    )

    if (
        has_petroleum
        and has_spill_signal
    ):
        return EventCategory.oil_spill

    # --------------------------------------------------
    # Chemical release
    # --------------------------------------------------

    chemical_terms = [
        "chemical release",
        "chemical spill",
        "toxic release",
        "toxic leak",

        "химический выброс",
        "химическая утечка",
        "разлив химикатов",
        "токсичный выброс",
    ]

    if any(
        term in text
        for term in chemical_terms
    ):
        return EventCategory.chemical_release

    # --------------------------------------------------
    # General water pollution
    # --------------------------------------------------

    water_pollution_terms = [
        "water pollution",
        "marine pollution",
        "contamination",
        "sewage",
        "contaminated runoff",
        "algae bloom",

        "загрязнение моря",
        "загрязнение воды",
        "загрязнение акватории",
        "сточные воды",
        "стоки",
        "цветение воды",
    ]

    if any(
        term in text
        for term in water_pollution_terms
    ):
        return EventCategory.water_pollution

    return None


def detect_location(text: str):

    text = text.lower()

    locations = {
        "odesa": "Odesa",
        "odessa": "Odesa",
        "одесса": "Odesa",
        "одеса": "Odesa",

        "anapa": "Anapa",
        "анапа": "Anapa",
        "анапский": "Anapa",

        "novorossiysk": "Novorossiysk",
        "новороссийск": "Novorossiysk",

        "gelendzhik": "Gelendzhik",
        "геленджик": "Gelendzhik",

        "tuapse": "Tuapse",
        "туапсе": "Tuapse",

        "sochi": "Sochi",
        "сочи": "Sochi",

        "bulgaria": "Bulgaria",
        "болгария": "Bulgaria",

        "varna": "Varna",
        "варна": "Varna",

        "burgas": "Burgas",
        "бургас": "Burgas",

        "romania": "Romania",
        "румыния": "Romania",

        "constanta": "Constanta",
        "констанца": "Constanta",

        "crimea": "Crimea",
        "крым": "Crimea",

        "sevastopol": "Sevastopol",
        "севастополь": "Sevastopol",

        "kerch": "Kerch Strait",
        "керч": "Kerch Strait",

        "kherson": "Kherson",
        "херсон": "Kherson",

        "batumi": "Batumi",
        "батуми": "Batumi",

        "trabzon": "Trabzon",
        "трабзон": "Trabzon",

        "krasnodar krai": "Krasnodar Krai",
        "краснодарский край": "Krasnodar Krai",
    }

    for keyword, location in locations.items():

        if keyword in text:
            return location

    if (
        "black sea" in text
        or "черное море" in text
        or "чёрное море" in text
    ):
        return "Black Sea"

    return None


def classify_news_item(
    item: NewsItem
) -> NewsClassification:

    text = (
        f"{item.title} "
        f"{item.summary or ''}"
    ).lower()

    category = detect_category(
        text
    )

    location = detect_location(
        text
    )

    # --------------------------------------------------
    # Explicit absence of pollution
    # --------------------------------------------------

    clear_terms = [
        "no signs of active pollution",
        "no pollution detected",
        "waters clean",
        "no contamination detected",

        "загрязнение не выявлено",
        "загрязнений не выявлено",
        "следов загрязнения не обнаружено",
        "вода соответствует норме",
    ]

    if any(
        phrase in text
        for phrase in clear_terms
    ):
        return NewsClassification(
            classification=NewsClassificationType.clear,
            category=category,
            location_name=location,
            confidence=0.90,
            is_new_event=False,
            event_date=None,
            reason=(
                "The report explicitly states that "
                "active pollution was not detected."
            ),
        )

    # --------------------------------------------------
    # Forecast / future threat
    # --------------------------------------------------

    forecast_terms = [
        "could trigger",
        "could cause",
        "may cause",
        "risk of pollution",
        "threat of pollution",

        "может привести",
        "может вызвать",
        "угроза загрязнения",
        "риск загрязнения",
    ]

    if any(
        phrase in text
        for phrase in forecast_terms
    ):
        return NewsClassification(
            classification=NewsClassificationType.forecast,
            category=category,
            location_name=location,
            confidence=0.80,
            is_new_event=False,
            event_date=None,
            reason=(
                "The report describes a possible future "
                "environmental impact."
            ),
        )

    # --------------------------------------------------
    # Follow-up / extinguished / localized / cleanup
    # --------------------------------------------------

    follow_up_terms = [
        "cleanup",
        "reopen",
        "ongoing environmental impact",
        "aftermath",
        "recovery",
        "extinguished",
        "contained",

        "ликвидирован",
        "ликвидировали",
        "потушили",
        "потушен",
        "локализован",
        "локализовали",
        "ликвидация последствий",
        "очистка",
        "уборка мазута",
        "восстановлено",
        "восстановили",
    ]

    if any(
        phrase in text
        for phrase in follow_up_terms
    ):
        if category is not None:
            return NewsClassification(
                classification=NewsClassificationType.follow_up,
                category=category,
                location_name=location,
                confidence=0.80,
                is_new_event=False,
                event_date=None,
                reason=(
                    "The report concerns response, containment "
                    "or consequences of an earlier incident."
                ),
            )

    # --------------------------------------------------
    # General programmes / research / policy
    # --------------------------------------------------

    background_terms = [
        "addressing pollution",
        "empowering the black sea",
        "climate agenda",
        "strategy",
        "programme",
        "program",
        "project officially launched",
        "monitoring of black sea pollution",

        "исследование",
        "мониторинг состояния",
        "проект запущен",
        "программа",
        "стратегия",
    ]

    if any(
        phrase in text
        for phrase in background_terms
    ):
        return NewsClassification(
            classification=NewsClassificationType.background,
            category=category,
            location_name=location,
            confidence=0.75,
            is_new_event=False,
            event_date=None,
            reason=(
                "The article discusses environmental issues "
                "generally rather than a specific incident."
            ),
        )

    # --------------------------------------------------
    # Unconfirmed reports
    # --------------------------------------------------

    reported_terms = [
        "reports of oil pollution",
        "checks reports",
        "responds to reports",
        "investigating reports",
        "suspected pollution",
        "possible spill",

        "сообщения о загрязнении",
        "проверяют сообщения",
        "проверяет сообщения",
        "возможный разлив",
        "предполагаемый разлив",
        "подозрение на загрязнение",
    ]

    if any(
        phrase in text
        for phrase in reported_terms
    ):
        return NewsClassification(
            classification=NewsClassificationType.reported,
            category=category,
            location_name=location,
            confidence=0.75,
            is_new_event=None,
            event_date=None,
            reason=(
                "A possible incident has been reported "
                "but is still being investigated."
            ),
        )

    # --------------------------------------------------
    # Wildfire
    # --------------------------------------------------

    if category == EventCategory.wildfire:

        wildfire_active_terms = [
            "wildfire",
            "forest fire",
            "vegetation fire",
            "brush fire",

            "лесной пожар",
            "лесных пожара",
            "лесных пожаров",
            "природный пожар",
            "ландшафтный пожар",
            "пожар в лесном массиве",
            "горит лес",
            "лес горит",
            "тушат",
            "тушат с воздуха",
        ]

        if any(
            phrase in text
            for phrase in wildfire_active_terms
        ):
            return NewsClassification(
                classification=NewsClassificationType.incident,
                category=category,
                location_name=location,
                confidence=0.80,
                is_new_event=None,
                event_date=None,
                reason=(
                    "The article describes an active "
                    "wildfire or vegetation fire."
                ),
            )

    # --------------------------------------------------
    # Industrial fire
    # --------------------------------------------------

    if category == EventCategory.industrial_fire:

        industrial_fire_active_terms = [
            "fire",
            "burning",

            "пожар",
            "пожаре",
            "возгора",
            "горит",
            "горел",
        ]

        if any(
            phrase in text
            for phrase in industrial_fire_active_terms
        ):
            return NewsClassification(
                classification=NewsClassificationType.incident,
                category=category,
                location_name=location,
                confidence=0.80,
                is_new_event=None,
                event_date=None,
                reason=(
                    "The article describes an active "
                    "industrial or infrastructure fire."
                ),
            )

    # --------------------------------------------------
    # Pollution / release incidents
    # --------------------------------------------------

    if category in {
        EventCategory.oil_spill,
        EventCategory.water_pollution,
        EventCategory.chemical_release,
    }:

        pollution_incident_terms = [
            "spill into",
            "oil spill",
            "contaminated runoff",
            "chemical release",
            "contamination",
            "pollution",

            "разлив",
            "утечк",
            "выброс",
            "загрязнение акватории",
            "загрязнение моря",
            "загрязнение воды",
        ]

        if any(
            phrase in text
            for phrase in pollution_incident_terms
        ):
            return NewsClassification(
                classification=NewsClassificationType.incident,
                category=category,
                location_name=location,
                confidence=0.80,
                is_new_event=None,
                event_date=None,
                reason=(
                    "The article describes an environmental "
                    "pollution or release incident."
                ),
            )

    return NewsClassification(
        classification=NewsClassificationType.noise,
        category=category,
        location_name=location,
        confidence=0.60,
        is_new_event=False,
        event_date=None,
        reason=(
            "No specific environmental incident was "
            "identified by the rule-based classifier."
        ),
    )