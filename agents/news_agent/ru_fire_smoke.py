from agents.news_agent.models import NewsItem

from agents.news_agent.rule_classifier import (
    classify_news_item,
)

from agents.news_agent.llm_classifier import (
    classify_news_with_llm,
)

from agents.news_agent.lifecycle_guard import (
    apply_lifecycle_guard,
)

from agents.news_agent.event_gate import (
    evaluate_event_candidate,
)


TEST_ITEMS = [

    NewsItem(
        title=(
            "Сразу три лесных пожара "
            "тушат в Новороссийске"
        ),
        url="https://example.com/wildfire-active",
        source="Test Source",
        published_at="Thu, 10 Sep 2026 07:00:00 GMT",
        summary=None,
    ),

    NewsItem(
        title=(
            "Лесной пожар возле хутора Дюрсо "
            "под Новороссийском ликвидирован"
        ),
        url="https://example.com/wildfire-followup",
        source="Test Source",
        published_at="Thu, 10 Sep 2026 07:00:00 GMT",
        summary=None,
    ),

    NewsItem(
        title=(
            "Новороссийск атаковали беспилотники, "
            "сообщается о пожаре "
            "на мазутном терминале"
        ),
        url="https://example.com/industrial-fire",
        source="Test Source",
        published_at="Thu, 10 Sep 2026 07:00:00 GMT",
        summary=None,
    ),

    NewsItem(
        title=(
            "Мужчина и женщина погибли "
            "при пожаре в доме"
        ),
        url="https://example.com/residential-fire",
        source="Test Source",
        published_at="Thu, 10 Sep 2026 07:00:00 GMT",
        summary=None,
    ),
]


def print_result(
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

    for index, item in enumerate(
        TEST_ITEMS,
        start=1,
    ):

        print("=" * 80)

        print(
            f"{index}. {item.title}"
        )

        print()

        # ----------------------------------------------
        # Rule-based
        # ----------------------------------------------

        rule_result = classify_news_item(
            item
        )

        print_result(
            "RULE-BASED",
            rule_result,
        )

        print()

        # ----------------------------------------------
        # LLM
        # ----------------------------------------------

        try:

            llm_result = classify_news_with_llm(
                item
            )

            print_result(
                "LLM RAW",
                llm_result,
            )

            print()

            # ------------------------------------------
            # Lifecycle Guard
            # ------------------------------------------

            guarded_result = apply_lifecycle_guard(
                item,
                llm_result,
            )

            print_result(
                "AFTER LIFECYCLE GUARD",
                guarded_result,
            )

            print()

            # ------------------------------------------
            # Event Gate
            # ------------------------------------------

            gate_decision = evaluate_event_candidate(
                guarded_result
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


if __name__ == "__main__":
    main()