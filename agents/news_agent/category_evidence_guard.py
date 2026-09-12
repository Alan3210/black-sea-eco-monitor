from agents.news_agent.classification import NewsClassification
from agents.news_agent.models import NewsItem
from backend.models.event import EventCategory


INDUSTRIAL_FIRE_SIGNALS = [
    "terminal",
    "refinery",
    "factory",
    "industrial plant",
    "fuel depot",
    "oil depot",
    "power plant",
    "substation",
    "port terminal",
    "fuel storage",

    "терминал",
    "нефтебаз",
    "завод",
    "предприят",
    "промышлен",
    "подстанц",
    "электростанц",
    "тэц",
    "резервуар",
    "склад гсм",
    "топливн",
    "в порту",
    "на территории порта",
    "портовый терминал",
]


FIRE_SIGNALS = [
    "fire",
    "burning",
    "blaze",
    "пожар",
    "возгора",
    "горит",
    "горел",
]


def _build_text(
    item: NewsItem
) -> str:

    return (
        f"{item.title} "
        f"{item.summary or ''}"
    ).lower()


def apply_category_evidence_guard(
    item: NewsItem,
    classification: NewsClassification,
) -> NewsClassification:
    """
    Deterministic guard against unsupported LLM categories.

    The first protected category is industrial_fire because the
    LLM can otherwise infer industrial infrastructure from context
    such as a port city, military attack, or proximity to the sea.
    """

    if (
        classification.category
        != EventCategory.industrial_fire
    ):
        return classification

    text = _build_text(
        item
    )

    has_fire_signal = any(
        term in text
        for term in FIRE_SIGNALS
    )

    has_industrial_signal = any(
        term in text
        for term in INDUSTRIAL_FIRE_SIGNALS
    )

    if (
        has_fire_signal
        and has_industrial_signal
    ):
        return classification

    return classification.model_copy(
        update={
            "category": None,
            "confidence": min(
                classification.confidence,
                0.69,
            ),
            "reason": (
                "Industrial-fire category removed: "
                "the supplied text does not identify "
                "industrial, energy, transport, or fuel infrastructure."
            ),
        }
    )
