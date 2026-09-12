from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)


MIN_CONFIDENCE_ON_RULE_AGREEMENT = 0.80


def apply_incident_evidence_guard(
    llm_result: NewsClassification,
    rule_result: NewsClassification,
) -> NewsClassification:
    """
    Strengthen a candidate only when the semantic and deterministic
    layers agree that it is a real categorized Black Sea incident.

    This guard runs after the category and lifecycle guards.

    It does NOT promote:
    - uncategorized incidents;
    - incidents outside / unconfirmed for the Black Sea region;
    - follow-ups, noise, background, forecast or clear reports.
    """

    if (
        llm_result.classification
        != NewsClassificationType.incident
    ):
        return llm_result

    if llm_result.category is None:
        return llm_result

    if llm_result.is_black_sea_region is not True:
        return llm_result

    updates = {}

    if llm_result.is_new_event is None:
        updates["is_new_event"] = True

    if (
        rule_result.classification
        == NewsClassificationType.incident
        and rule_result.category
        == llm_result.category
        and llm_result.confidence
        < MIN_CONFIDENCE_ON_RULE_AGREEMENT
    ):
        updates["confidence"] = (
            MIN_CONFIDENCE_ON_RULE_AGREEMENT
        )

    if not updates:
        return llm_result

    return llm_result.model_copy(
        update=updates
    )
