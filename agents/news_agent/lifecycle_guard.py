from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)

from agents.news_agent.models import NewsItem


CLEAR_TERMS = [
    # English
    "no signs of active pollution",
    "no pollution detected",
    "no contamination detected",
    "waters clean",
    "water is clean",

    # Russian
    "загрязнение не выявлено",
    "загрязнений не выявлено",
    "загрязнение не обнаружено",
    "следов загрязнения не обнаружено",
    "следов загрязнения не выявлено",
    "вода соответствует норме",
]


COMPLETED_TERMS = [

    # English
    "cleanup completed",
    "extinguished",
    "contained",
    "reopened",
    "reopen",
    "recovery",
    "aftermath",

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
    "локализовали",

    "ликвидация последствий",

    "очистка",
    "очищен",
    "очищена",
    "очищены",

    "уборка мазута",

    "восстановлен",
    "восстановлена",
    "восстановлено",
    "восстановили",

    "открыли пляжи",
    "открытие пляжей",
]


ACTIVE_RESPONSE_TERMS = [

    # English
    "cleanup",
    "containing",
    "controlling",
    "firefighting",

    # Russian
    "ликвидируют",
    "тушат",
    "тушится",
    "ведется тушение",
    "ведётся тушение",
    "проводится тушение",
    "идет тушение",
    "идёт тушение",
]

def build_lifecycle_text(
    item: NewsItem
) -> str:

    return (
        f"{item.title} "
        f"{item.summary or ''}"
    ).lower()


def apply_lifecycle_guard(
    item: NewsItem,
    classification: NewsClassification,
) -> NewsClassification:

    text = build_lifecycle_text(
        item
    )

    # --------------------------------------------------
    # CLEAR has highest priority.
    # --------------------------------------------------

    if any(
        term in text
        for term in CLEAR_TERMS
    ):

        return classification.model_copy(
            update={
                "classification":
                    NewsClassificationType.clear,

                "is_new_event":
                    False,

                "reason": (
                    "Lifecycle Guard: the source explicitly "
                    "states that active pollution or "
                    "contamination was not detected."
                ),
            }
        )

    # --------------------------------------------------
    # Explicitly completed / contained incident.
    # --------------------------------------------------

    if any(
        term in text
        for term in COMPLETED_TERMS
    ):

        return classification.model_copy(
            update={
                "classification":
                    NewsClassificationType.follow_up,

                "is_new_event":
                    False,

                "reason": (
                    "Lifecycle Guard: explicit wording "
                    "indicates response, containment, "
                    "cleanup or completion of an earlier "
                    "environmental incident."
                ),
            }
        )
        if any(
            term in text
            for term in ACTIVE_RESPONSE_TERMS
        ):

            return classification.model_copy(
                update={
                    "is_new_event": True,

                    "reason": (
                        "Lifecycle Guard: the wording indicates "
                        "active response or firefighting is "
                        "currently ongoing."
                    ),
                }
            )


    # --------------------------------------------------
    # No deterministic lifecycle signal.
    # Keep LLM result unchanged.
    # --------------------------------------------------

    return classification