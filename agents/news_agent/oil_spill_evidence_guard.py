import re

from agents.news_agent.classification import NewsClassification
from backend.models.event import EventCategory


OIL_SPILL_POSITIVE_MARKERS = [
    "spill",
    "leak",
    "leakage",
    "discharge",
    "разлив",
    "утечка",
    "выброс",
    "попало в море",
    "загрязнение воды",
    "загрязнение моря",
    "нефтяное пятно",
    "мазутное пятно",
    "oil pollution",
    "oil spill",
]


OIL_SPILL_CONTEXT_NEGATIVE_MARKERS = [
    "суд",
    "иск",
    "штраф",
    "компенсац",
    "ответственност",
    "владельц",
    "страхов",
    "юрист",
    "претенз",
    "взыск",
    "liability",
    "lawsuit",
    "compensation",
]


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(
        r"[^a-zа-яё0-9\s]+",
        " ",
        text,
    )
    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def apply_oil_spill_evidence_guard(
    item,
    classification: NewsClassification,
) -> NewsClassification:
    """
    Prevent oil_spill classification based only on historical/legal
    references to previous pollution events.

    An active oil spill requires evidence of an actual release,
    leakage or contamination.
    """

    if classification.category != EventCategory.oil_spill:
        return classification

    text = " ".join(
        filter(
            None,
            [
                getattr(item, "title", ""),
                getattr(item, "summary", ""),
            ],
        )
    )

    normalized = _normalize_text(text)

    has_positive_marker = any(
        marker in normalized
        for marker in OIL_SPILL_POSITIVE_MARKERS
    )

    has_negative_context = any(
        marker in normalized
        for marker in OIL_SPILL_CONTEXT_NEGATIVE_MARKERS
    )

    if has_positive_marker:
        return classification

    if has_negative_context or not has_positive_marker:
        return classification.model_copy(
            update={
                "category": None,
                "reason": (
                    "Oil spill category removed: "
                    "no evidence of active release or "
                    "water contamination was found."
                ),
            }
        )

    return classification
