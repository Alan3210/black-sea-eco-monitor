from agents.news_agent.agent import NewsAgent


def main():

    agent = NewsAgent()

    print(
        f"Starting {agent.name}..."
    )


    items = agent.collect()


    print(
        f"Collected {len(items)} news items."
    )


    print()


    for index, item in enumerate(
        items[:5],
        start=1
    ):

        print(
            f"{index}. {item.title}"
        )

        print(
            f"   Source: {item.source}"
        )

        print(
            f"   Published: {item.published_at}"
        )

        print(
            f"   URL: {item.url}"
        )

        print()


if __name__ == "__main__":
    main()