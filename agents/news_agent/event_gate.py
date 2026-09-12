from enum import Enum

from pydantic import BaseModel

from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)


class EventGateAction(str, Enum):
    create_event = "create_event"
    attach_follow_up = "attach_follow_up"
    ignore = "ignore"


class EventGateDecision(BaseModel):
    action: EventGateAction
    reason: str


MIN_EVENT_CONFIDENCE = 0.75


def evaluate_event_candidate(
    classification: NewsClassification,
) -> EventGateDecision:

    # ---------------------------------------------
    # Follow-up information about an existing event
    # ---------------------------------------------

    if (
        classification.classification
        == NewsClassificationType.follow_up
    ):

        if classification.is_black_sea_region is True:

            return EventGateDecision(
                action=EventGateAction.attach_follow_up,
                reason=(
                    "The article is a Black Sea follow-up "
                    "and should be attached to an existing event."
                ),
            )

        return EventGateDecision(
            action=EventGateAction.ignore,
            reason=(
                "The article is a follow-up but is not confirmed "
                "to belong to the Black Sea region."
            ),
        )

    # ---------------------------------------------
    # Classes that must never create a new event
    # ---------------------------------------------

    if classification.classification in {
        NewsClassificationType.clear,
        NewsClassificationType.background,
        NewsClassificationType.forecast,
        NewsClassificationType.noise,
    }:

        return EventGateDecision(
            action=EventGateAction.ignore,
            reason=(
                f"Classification "
                f"'{classification.classification.value}' "
                f"does not create a new environmental event."
            ),
        )

    # ---------------------------------------------
    # Only incident / reported reach this point
    # ---------------------------------------------

    if classification.classification not in {
        NewsClassificationType.incident,
        NewsClassificationType.reported,
    }:

        return EventGateDecision(
            action=EventGateAction.ignore,
            reason="Unsupported classification.",
        )

    # ---------------------------------------------
    # Geography gate
    # ---------------------------------------------

    if classification.is_black_sea_region is not True:

        return EventGateDecision(
            action=EventGateAction.ignore,
            reason=(
                "The environmental incident is not confirmed "
                "to be in the Black Sea region."
            ),
        )

    # ---------------------------------------------
    # New-event gate
    # ---------------------------------------------

    if classification.is_new_event is not True:

        return EventGateDecision(
            action=EventGateAction.ignore,
            reason=(
                "The article does not reliably describe "
                "a new environmental event."
            ),
        )

    # ---------------------------------------------
    # Confidence gate
    # ---------------------------------------------

    if classification.confidence < MIN_EVENT_CONFIDENCE:

        return EventGateDecision(
            action=EventGateAction.ignore,
            reason=(
                f"Confidence {classification.confidence:.2f} "
                f"is below the minimum threshold "
                f"{MIN_EVENT_CONFIDENCE:.2f}."
            ),
        )

    # ---------------------------------------------
    # Required environmental category
    # ---------------------------------------------

    if classification.category is None:

        return EventGateDecision(
            action=EventGateAction.ignore,
            reason=(
                "The candidate passed semantic checks "
                "but has no environmental category."
            ),
        )

    # ---------------------------------------------
    # Candidate accepted
    # ---------------------------------------------

    return EventGateDecision(
        action=EventGateAction.create_event,
        reason=(
            "The article describes a sufficiently confident, "
            "new Black Sea environmental event."
        ),
    )