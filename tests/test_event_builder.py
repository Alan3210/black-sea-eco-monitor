from agents.news_agent.event_builder import (
    build_environmental_event,
)

from agents.news_agent.models import (
    NewsItem,
)

from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)

from backend.models.event import (
    EventCategory,
)



def test_build_event_from_news():

    item = NewsItem(

        title=
        "Forest fire near Novorossiysk",

        url=
        "https://example.com",

        source=
        "Test News",

        published_at=
        "Thu, 10 Sep 2026 07:00:00 GMT",

        summary=None
    )


    classification = NewsClassification(

        classification=
        NewsClassificationType.incident,

        category=
        EventCategory.wildfire,

        location_name=
        "Novorossiysk",

        is_black_sea_region=
        True,

        confidence=
        0.9,

        is_new_event=
        True,

        event_date=
        None,

        reason=
        "Active wildfire detected."
    )


    event = build_environmental_event(
        item,
        classification
    )


    assert (
        event.category
        ==
        EventCategory.wildfire
    )


    assert (
        len(event.evidences)
        ==
        1
    )


    assert (
        event.evidences[0]
        .source
        .name
        ==
        "Test News"
    )