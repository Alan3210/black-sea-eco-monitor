from agents.news_agent.models import NewsItem

from agents.news_agent.llm_classifier import (
    classify_news_with_llm,
)


def main():

    item = NewsItem(

        title=(
            "Thousands of Tons of Sunflower Oil "
            "Spill Into Black Sea After Kremlin "
            "Hits Odesa Region Port"
        ),

        url="https://example.com",

        source="Kyiv Post",

        published_at="2026-09-10",

        summary=None
    )


    result = classify_news_with_llm(
        item
    )


    print()
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()