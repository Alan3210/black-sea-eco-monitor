from agents.news_agent.agent import NewsAgent

from agents.news_agent.filter import (
    filter_black_sea_incidents,
)

from agents.news_agent.rule_classifier import (
    classify_news_item,
)

from agents.news_agent.llm_classifier import (
    classify_news_with_llm,
)

from agents.news_agent.event_gate import (
    evaluate_event_candidate,
)

from agents.news_agent.freshness_gate import (
    evaluate_news_freshness,
)


# Maximum number of FRESH candidates
# that will be sent to the LLM.
#
# None = process all fresh candidates.
BATCH_LIMIT = 5


def main():

    agent = NewsAgent()

    print("Collecting news...")
    print()

    # --------------------------------------------------
    # 1. Collect RSS news
    # --------------------------------------------------

    items = agent.collect()

    print(
        f"Collected: {len(items)}"
    )

    # --------------------------------------------------
    # 2. Environmental pre-filter
    # --------------------------------------------------

    relevant_items = agent.analyze(
        items
    )

    print(
        f"Environmentally relevant: "
        f"{len(relevant_items)}"
    )

    # --------------------------------------------------
    # 3. Black Sea candidate pre-filter
    # --------------------------------------------------

    candidates = filter_black_sea_incidents(
        relevant_items
    )

    print(
        f"Black Sea candidates: "
        f"{len(candidates)}"
    )

    print()

    # --------------------------------------------------
    # 4. Freshness filter
    # --------------------------------------------------

    fresh_candidates = []

    print("FRESHNESS CHECK")
    print()

    for index, item in enumerate(
        candidates,
        start=1
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

    # --------------------------------------------------
    # 5. Limit expensive LLM processing
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 6. Rule-Based + LLM + Event Gate
    # --------------------------------------------------

    for index, item in enumerate(
        selected_candidates,
        start=1
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

        # ----------------------------------------------
        # Rule-based classification
        # ----------------------------------------------

        rule_result = classify_news_item(
            item
        )

        print("RULE-BASED")

        print(
            f"  Classification: "
            f"{rule_result.classification.value}"
        )

        print(
            f"  Category: "
            f"{rule_result.category}"
        )

        print(
            f"  Location: "
            f"{rule_result.location_name}"
        )

        print(
            f"  Black Sea region: "
            f"{rule_result.is_black_sea_region}"
        )

        print(
            f"  New event: "
            f"{rule_result.is_new_event}"
        )

        print(
            f"  Event date: "
            f"{rule_result.event_date}"
        )

        print(
            f"  Confidence: "
            f"{rule_result.confidence}"
        )

        print()

        # ----------------------------------------------
        # LLM classification
        # ----------------------------------------------

        try:

            llm_result = (
                classify_news_with_llm(
                    item
                )
            )

            print("LLM")

            print(
                f"  Classification: "
                f"{llm_result.classification.value}"
            )

            print(
                f"  Category: "
                f"{llm_result.category}"
            )

            print(
                f"  Location: "
                f"{llm_result.location_name}"
            )

            print(
                f"  Black Sea region: "
                f"{llm_result.is_black_sea_region}"
            )

            print(
                f"  Confidence: "
                f"{llm_result.confidence}"
            )

            print(
                f"  New event: "
                f"{llm_result.is_new_event}"
            )

            print(
                f"  Event date: "
                f"{llm_result.event_date}"
            )

            print(
                f"  Reason: "
                f"{llm_result.reason}"
            )

            print()

            # ------------------------------------------
            # Event Gate
            # ------------------------------------------

            gate_decision = (
                evaluate_event_candidate(
                    llm_result
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