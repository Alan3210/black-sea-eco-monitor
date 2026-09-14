import re

from agents.news_agent.classification import (
    NewsClassificationType,
)


LEGAL_FOLLOW_UP_PATTERNS = (
    r"\bуточненн\w*\s+иск\w*\b",
    r"\bиск\w*\s+(?:к|против)\b",
    r"\bсудовладел\w*\b",
    r"\bарбитражн\w*\s+суд\w*\b",
    r"\bрешени\w*\s+суд\w*\b",
    r"\bсуд\w*\s+(?:принял|рассматривает|рассмотрит|"
    r"удовлетворил|взыскал|обязал)\b",
    r"\b(?:компенсац\w*|возмещени\w*\s+ущерб\w*|"
    r"взыскани\w*\s+ущерб\w*)\b",
    r"\b(?:lawsuit|legal claim|court claim|damages claim)\b",
    r"\bcourt\s+(?:accepted|heard|will hear|ordered|awarded)\b",
    r"\bcompensation\s+(?:claim|case)\b",
    r"\bshipowner(?:s)?\b.*\b(?:claim|lawsuit|court)\b",
)


def _build_text(item) -> str:
    return " ".join(
        part
        for part in (
            getattr(item, "title", None),
            getattr(item, "summary", None),
        )
        if part
    ).lower()


def has_legal_follow_up_signal(item) -> bool:
    text = _build_text(item)

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in LEGAL_FOLLOW_UP_PATTERNS
    )


def apply_legal_followup_guard(
    item,
    result,
):
    """
    Convert litigation/compensation coverage about an environmental
    incident into follow_up.

    The guard is deliberately deterministic and runs after the general
    incident-evidence guard, so legal aftermath cannot be promoted back
    into a new incident by a broader classifier.
    """

    if result.category is None:
        return result

    if result.classification in {
        NewsClassificationType.background,
        NewsClassificationType.forecast,
        NewsClassificationType.clear,
        NewsClassificationType.noise,
    }:
        return result

    if not has_legal_follow_up_signal(item):
        return result

    return result.model_copy(
        update={
            "classification":
            NewsClassificationType.follow_up,
            "is_new_event": False,
            "reason": (
                "Legal Follow-up Guard: the article concerns "
                "litigation, compensation or liability after "
                "an environmental incident."
            ),
        }
    )
