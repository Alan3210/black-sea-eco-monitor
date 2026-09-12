from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)

from backend.models.event import EventCategory
from agents.news_agent.models import NewsItem


def build_text(
    item: NewsItem
) -> str:

    return (
        f"{item.title} "
        f"{item.summary or ''}"
    ).lower()


# =====================================================
# CATEGORY DETECTION
# =====================================================


def detect_category(
    text: str
):

    # -------------------------------
    # Industrial fire
    # -------------------------------

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
        "factory",
        "plant",
        "industrial",
        "fuel depot",
        "oil depot",

        "терминал",
        "нефтебаз",
        "завод",
        "предприят",
        "промышлен",
        "порт",
        "подстанц",
        "резервуар",
    ]

    if (
        any(
            term in text
            for term in fire_terms
        )
        and
        any(
            term in text
            for term in industrial_terms
        )
    ):
        return EventCategory.industrial_fire

    # -------------------------------
    # Wildfire
    # -------------------------------

    direct_wildfire_terms = [
        "wildfire",
        "forest fire",

        "лесопожар",
        "природный пожар",
        "пожар в лесном массиве",
    ]

    has_fire_signal = any(
        term in text
        for term in [
            "fire",
            "пожар",
            "возгора",
            "горит",
            "горел",
        ]
    )

    has_forest_context = any(
        term in text
        for term in [
            "лесн",
            "заповедник",
            "утриш",
        ]
    )

    if (
        any(
            term in text
            for term in direct_wildfire_terms
        )
        or (
            has_fire_signal
            and has_forest_context
        )
    ):
        return EventCategory.wildfire

    # -------------------------------
    # Edible oil
    # -------------------------------

    edible_oil_terms = [
        "sunflower oil",
        "vegetable oil",

        "подсолнечное масло",
        "растительное масло",
    ]

    if any(
        term in text
        for term in edible_oil_terms
    ):
        return EventCategory.water_pollution

    # -------------------------------
    # Oil spill
    # -------------------------------

    oil_terms = [
        "crude oil",
        "fuel oil",
        "petroleum",
        "hydrocarbon",

        "нефть",
        "мазут",
        "нефтепродукт",
    ]

    spill_terms = [
        "spill",
        "leak",
        "pollution",

        "разлив",
        "утечк",
        "загрязн",
    ]

    if (
        any(
            term in text
            for term in oil_terms
        )
        and
        any(
            term in text
            for term in spill_terms
        )
    ):
        return EventCategory.oil_spill

    # -------------------------------
    # Chemical
    # -------------------------------

    chemical_terms = [
        "chemical release",
        "chemical spill",

        "химический выброс",
        "разлив химикатов",
    ]

    if any(
        term in text
        for term in chemical_terms
    ):
        return EventCategory.chemical_release

    # -------------------------------
    # General water pollution
    # -------------------------------

    pollution_terms = [
        "marine pollution",
        "water pollution",
        "contamination",
        "sewage",

        "загрязнение моря",
        "загрязнение воды",
        "сточные воды",
    ]

    if any(
        term in text
        for term in pollution_terms
    ):
        return EventCategory.water_pollution

    return None


# =====================================================
# INCIDENT SIGNAL DETECTION
# =====================================================


def detect_incident_signal(
    text: str
) -> bool:

    incident_terms = [

        # English

        "fire",
        "wildfire",
        "burning",
        "firefighters",
        "extinguished",
        "contained",
        "spill",
        "leak",
        "pollution",
        "contamination",

        # Russian

        "пожар",
        "возгора",
        "горит",
        "горел",

        "огнеборцы",
        "пожарные",

        "тушат",
        "тушится",
        "ликвидируют",

        "ликвидирован",
        "локализован",

        "потушен",
        "потушили",

        "разлив",
        "утечк",

        "загрязнен",
        "загрязнён",
    ]

    return any(
        term in text
        for term in incident_terms
    )


# =====================================================
# LOCATION DETECTION
# =====================================================


def detect_location(
    text: str
):

    # More specific locations come before broader regions.

    locations = {

        "novorossiysk":
        "Novorossiysk",

        "новороссийск":
        "Novorossiysk",


        "sevastopol":
        "Sevastopol",

        "севастополь":
        "Sevastopol",


        "gelendzhik":
        "Gelendzhik",

        "геленджик":
        "Gelendzhik",


        "anapa":
        "Anapa",

        "анап":
        "Anapa",


        "tuapse":
        "Tuapse",

        "туапсе":
        "Tuapse",


        "sochi":
        "Sochi",

        "сочи":
        "Sochi",


        "odesa":
        "Odesa",

        "odessa":
        "Odesa",

        "одесс":
        "Odesa",


        "varna":
        "Varna",

        "варн":
        "Varna",


        "burgas":
        "Burgas",

        "бургас":
        "Burgas",


        "constanta":
        "Constanta",

        "constanța":
        "Constanta",

        "констанц":
        "Constanta",


        "kerch":
        "Kerch Strait",

        "керч":
        "Kerch Strait",


        "kherson":
        "Kherson",

        "херсон":
        "Kherson",


        "batumi":
        "Batumi",

        "батуми":
        "Batumi",


        "trabzon":
        "Trabzon",

        "трабзон":
        "Trabzon",


        "krasnodar krai":
        "Krasnodar Krai",

        "krasnodar region":
        "Krasnodar Krai",

        "краснодарский край":
        "Krasnodar Krai",

        "кубан":
        "Krasnodar Krai",


        "crimea":
        "Crimea",

        "крым":
        "Crimea",


        "bulgaria":
        "Bulgaria",

        "болгар":
        "Bulgaria",


        "romania":
        "Romania",

        "румын":
        "Romania",
    }

    for key, value in locations.items():

        if key in text:

            return value

    if (
        "black sea" in text
        or
        "черное море" in text
        or
        "чёрное море" in text
    ):

        return "Black Sea"

    return None


# =====================================================
# MAIN CLASSIFIER
# =====================================================


def classify_news_item(
    item: NewsItem
) -> NewsClassification:

    text = build_text(
        item
    )

    category = detect_category(
        text
    )

    location = detect_location(
        text
    )

    # ---------------------------------
    # Explicit clear reports
    # ---------------------------------

    if any(
        term in text
        for term in [
            "no pollution detected",
            "no contamination detected",
            "no signs of active pollution",
            "waters clean",

            "загрязнение не выявлено",
            "загрязнений не выявлено",
        ]
    ):

        return NewsClassification(
            classification=
            NewsClassificationType.clear,

            category=category,

            location_name=location,

            confidence=0.9,

            is_new_event=False,

            event_date=None,

            reason=
            "Pollution was explicitly not detected.",
        )

    # ---------------------------------
    # Background
    # ---------------------------------

    if any(
        term in text
        for term in [
            "research",
            "study",
            "programme",
            "program",
            "project",
            "strategy",

            "исследование",
            "программа",
            "проект",
            "стратегия",
        ]
    ):

        return NewsClassification(
            classification=
            NewsClassificationType.background,

            category=category,

            location_name=location,

            confidence=0.75,

            is_new_event=False,

            event_date=None,

            reason=
            "Background environmental information.",
        )

    # ---------------------------------
    # Ignore ordinary residential fires
    # ---------------------------------

    residential_terms = [
        "в доме",
        "в жилом доме",
        "в частном доме",
        "в квартире",
        "жилой дом",
        "частный дом",
        "квартира",

        "house fire",
        "apartment fire",
        "residential fire",
    ]

    fire_context_terms = [
        "пожар",
        "возгора",
        "fire",
    ]

    has_residential_context = any(
        term in text
        for term in residential_terms
    )

    has_fire_context = any(
        term in text
        for term in fire_context_terms
    )

    if (
        has_residential_context
        and has_fire_context
        and category is None
    ):

        return NewsClassification(
            classification=
            NewsClassificationType.noise,

            category=None,

            location_name=location,

            confidence=0.8,

            is_new_event=False,

            event_date=None,

            reason=(
                "Ordinary residential fire is not "
                "an environmental monitoring event."
            ),
        )

    # ---------------------------------
    # Completed / contained incidents
    # ---------------------------------

    completed_terms = [

        # English

        "extinguished",
        "contained",
        "cleanup completed",
        "recovery completed",

        # Russian

        "ликвидирован",
        "ликвидирована",
        "ликвидированы",
        "ликвидировали",

        "потушен",
        "потушена",
        "потушены",
        "потушили",

        "локализован",
        "локализована",
        "локализованы",

        "очищен",
        "очищена",
        "очищены",

        "убрана",
        "убран",

        "восстановлен",
        "восстановлена",
        "восстановлено",
        "восстановлены",
        "восстановили",
    ]

    if (
        any(
            term in text
            for term in completed_terms
        )
        and detect_incident_signal(
            text
        )
    ):

        return NewsClassification(
            classification=
            NewsClassificationType.follow_up,

            category=category,

            location_name=location,

            confidence=0.8,

            is_new_event=False,

            event_date=None,

            reason=(
                "The incident is completed, "
                "contained or in recovery."
            ),
        )

    # ---------------------------------
    # Candidate incident
    # ---------------------------------

    if detect_incident_signal(
        text
    ):

        return NewsClassification(
            classification=
            NewsClassificationType.incident,

            category=category,

            location_name=location,

            confidence=0.7,

            is_new_event=None,

            event_date=None,

            reason=
            "Potential environmental incident candidate.",
        )

    # ---------------------------------
    # Noise
    # ---------------------------------

    return NewsClassification(
        classification=
        NewsClassificationType.noise,

        category=category,

        location_name=location,

        confidence=0.6,

        is_new_event=False,

        event_date=None,

        reason=
        "No incident signal detected.",
    )