from agents.news_agent.agent import NewsAgent
from agents.news_agent.category_evidence_guard import (
    apply_category_evidence_guard,
)
from agents.news_agent.event_builder import (
    build_environmental_event,
)
from agents.news_agent.event_gate import (
    evaluate_event_candidate,
    EventGateAction,
)
from agents.news_agent.filter import (
    filter_black_sea_incidents,
)
from agents.news_agent.freshness_gate import (
    evaluate_news_freshness,
)
from agents.news_agent.incident_evidence_guard import (
    apply_incident_evidence_guard,
)
from agents.news_agent.lifecycle_guard import (
    apply_lifecycle_guard,
)
from agents.news_agent.llm_classifier import (
    classify_news_with_llm,
)
from agents.news_agent.rule_classifier import (
    classify_news_item,
)


BATCH_LIMIT = 5


def print_classification_result(
    label,
    result,
):

    print(label)

    print(
        f"  Classification: "
        f"{result.classification.value}"
    )

    print(
        f"  Category: "
        f"{result.category}"
    )

    print(
        f"  Location: "
        f"{result.location_name}"
    )

    print(
        f"  Black Sea region: "
        f"{result.is_black_sea_region}"
    )

    print(
        f"  Confidence: "
        f"{result.confidence}"
    )

    print(
        f"  New event: "
        f"{result.is_new_event}"
    )

    print(
        f"  Event date: "
        f"{result.event_date}"
    )

    print(
        f"  Reason: "
        f"{result.reason}"
    )


def main():

    agent = NewsAgent()

    print("Collecting news...")
    print()

    items = agent.collect()

    print(
        f"Collected: {len(items)}"
    )

    relevant_items = agent.analyze(
        items
    )

    print(
        f"Environmentally relevant: "
        f"{len(relevant_items)}"
    )

    candidates = filter_black_sea_incidents(
        relevant_items
    )

    print(
        f"Black Sea candidates: "
        f"{len(candidates)}"
    )

    print()

    fresh_candidates = []

    print("FRESHNESS CHECK")
    print()

    for index, item in enumerate(
        candidates,
        start=1,
    ):

        freshness = evaluate_news_freshness(
            item
        )

        print(
            f"{index}. {item.title}"
        )

        print(
            f"   Published: {item.published_at}"
        )

        print(
            f"   Fresh: {freshness.is_fresh}"
        )

        if freshness.age_days is not None:

            print(
                f"   Age: "
                f"{freshness.age_days:.1f} days"
            )

        print(
            f"   Reason: {freshness.reason}"
        )

        if freshness.is_fresh:

            fresh_candidates.append(
                item
            )

            print(
                "   PRELIMINARY ACTION: "
                "SEND_TO_LLM"
            )

        else:

            print(
                "   FINAL ACTION: "
                "IGNORE_STALE"
            )

        print()

    print("=" * 80)
    print()

    print(
        f"Fresh candidates: "
        f"{len(fresh_candidates)}"
    )

    if BATCH_LIMIT is None:

        selected_candidates = (
            fresh_candidates
        )

    else:

        selected_candidates = (
            fresh_candidates[:BATCH_LIMIT]
        )

    print(
        f"Processing with LLM: "
        f"{len(selected_candidates)}"
    )

    print()
    print("=" * 80)
    print()

    for index, item in enumerate(
        selected_candidates,
        start=1,
    ):

        print(
            f"{index}. {item.title}"
        )

        print(
            f"Source: {item.source}"
        )

        print(
            f"Published: {item.published_at}"
        )

        print()

        rule_result = classify_news_item(
            item
        )

        print_classification_result(
            "RULE-BASED",
            rule_result,
        )

        print()

        try:

            llm_result = classify_news_with_llm(
                item
            )

            print_classification_result(
                "LLM",
                llm_result,
            )

            print()

            category_guard_result = (
                apply_category_evidence_guard(
                    item,
                    llm_result,
                )
            )

            print_classification_result(
                "CATEGORY EVIDENCE GUARD",
                category_guard_result,
            )

            print()

            lifecycle_guard_result = (
                apply_lifecycle_guard(
                    item,
                    category_guard_result,
                )
            )

            print_classification_result(
                "LIFECYCLE GUARD",
                lifecycle_guard_result,
            )

            print()

            final_guarded_result = (
                apply_incident_evidence_guard(
                    lifecycle_guard_result,
                    rule_result,
                )
            )

            print_classification_result(
                "INCIDENT EVIDENCE GUARD",
                final_guarded_result,
            )

            print()

            gate_decision = (
                evaluate_event_candidate(
                    final_guarded_result
                )
            )

            print("EVENT GATE")

            print(
                f"  FINAL ACTION: "
                f"{gate_decision.action.value.upper()}"
            )

            print(
                f"  Reason: "
                f"{gate_decision.reason}"
            )

            if (
                gate_decision.action
                == EventGateAction.create_event
            ):

                event = build_environmental_event(
                    item,
                    final_guarded_result,
                )

                print()
                print("EVENT BUILDER")

                print(
                    event.model_dump_json(
                        indent=2
                    )
                )

        except Exception as error:

            print("LLM ERROR")

            print(
                f"  {type(error).__name__}: "
                f"{error}"
            )

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
