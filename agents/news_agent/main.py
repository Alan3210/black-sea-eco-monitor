from agents.news_agent.agent import NewsAgent
from agents.news_agent.filter import filter_black_sea_incidents
from agents.news_agent.rule_classifier import classify_news_item


def main():

    agent = NewsAgent()

    print(f"Starting {agent.name}...")
    print()

    # 1. Collect all news
    items = agent.collect()

    print(
        f"Collected news items: {len(items)}"
    )

    # 2. Environmental filter
    relevant_items = agent.analyze(items)

    print(
        f"Environmentally relevant: {len(relevant_items)}"
    )

    # 3. Black Sea incident candidates
    incident_items = filter_black_sea_incidents(
        relevant_items
    )

    print(
        f"Black Sea incident candidates: {len(incident_items)}"
    )

    print()

    # 4. Classify candidates
    for index, item in enumerate(
        incident_items,
        start=1
    ):

        classification = classify_news_item(
            item
        )

        print(
            f"{index}. "
            f"{classification.classification.value.upper()}"
        )

        print(
            f"   Category: {classification.category}"
        )

        print(
            f"   Location: {classification.location_name}"
        )

        print(
            f"   Confidence: {classification.confidence}"
        )

        print(
            f"   New event: {classification.is_new_event}"
        )

        print(
            f"   Event date: {classification.event_date}"
        )
        
        print(
            f"   Title: {item.title}"
        )

        print(
            f"   Reason: {classification.reason}"
        )

        print()


if __name__ == "__main__":
    main()