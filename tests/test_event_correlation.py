from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)
from agents.news_agent.event_correlation import (
    EventCandidate,
    cluster_event_candidates,
    evaluate_event_correlation,
)
from agents.news_agent.models import NewsItem
from backend.models.event import EventCategory


def make_item(
    title: str,
    published_at: str,
) -> NewsItem:

    return NewsItem(
        title=title,
        url="https://example.com",
        source="Test Source",
        published_at=published_at,
        summary=None,
    )


def make_classification(
    category: EventCategory,
    location: str,
) -> NewsClassification:

    return NewsClassification(
        classification=
        NewsClassificationType.incident,
        category=category,
        location_name=location,
        is_black_sea_region=True,
        confidence=0.9,
        is_new_event=True,
        event_date=None,
        reason="Test event.",
    )


def test_same_wildfire_is_correlated():

    first = EventCandidate(
        item=make_item(
            (
                "Площадь лесного пожара под "
                "Новороссийском увеличилась до 1,8 га"
            ),
            "Wed, 09 Sep 2026 10:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.wildfire,
            "Novorossiysk",
        ),
    )

    second = EventCandidate(
        item=make_item(
            (
                "Площадь пожара у Дюрсо в "
                "Новороссийске выросла до 1,8 га"
            ),
            "Wed, 09 Sep 2026 12:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.wildfire,
            "Novorossiysk",
        ),
    )

    decision = evaluate_event_correlation(
        first,
        second,
    )

    assert decision.is_same_event is True
    assert decision.similarity >= 0.45


def test_different_categories_are_not_correlated():

    wildfire = EventCandidate(
        item=make_item(
            "Лесной пожар под Новороссийском",
            "Wed, 09 Sep 2026 10:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.wildfire,
            "Novorossiysk",
        ),
    )

    industrial_fire = EventCandidate(
        item=make_item(
            "Большой пожар на терминале в Новороссийске",
            "Wed, 09 Sep 2026 11:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.industrial_fire,
            "Novorossiysk",
        ),
    )

    decision = evaluate_event_correlation(
        wildfire,
        industrial_fire,
    )

    assert decision.is_same_event is False


def test_different_locations_are_not_correlated():

    novorossiysk = EventCandidate(
        item=make_item(
            "Лесной пожар тушат с воздуха",
            "Wed, 09 Sep 2026 10:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.wildfire,
            "Novorossiysk",
        ),
    )

    anapa = EventCandidate(
        item=make_item(
            "Лесной пожар тушат с воздуха",
            "Wed, 09 Sep 2026 11:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.wildfire,
            "Anapa",
        ),
    )

    decision = evaluate_event_correlation(
        novorossiysk,
        anapa,
    )

    assert decision.is_same_event is False


def test_reports_outside_time_window_are_not_correlated():

    first = EventCandidate(
        item=make_item(
            "Пожар на терминале в Новороссийске",
            "Wed, 02 Sep 2026 10:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.industrial_fire,
            "Novorossiysk",
        ),
    )

    second = EventCandidate(
        item=make_item(
            "Пожар на терминале в Новороссийске",
            "Wed, 09 Sep 2026 10:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.industrial_fire,
            "Novorossiysk",
        ),
    )

    decision = evaluate_event_correlation(
        first,
        second,
    )

    assert decision.is_same_event is False


def test_cluster_groups_near_duplicate_reports():

    first = EventCandidate(
        item=make_item(
            (
                "Три лесных пожара тушат "
                "в Новороссийске"
            ),
            "Wed, 09 Sep 2026 10:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.wildfire,
            "Novorossiysk",
        ),
    )

    second = EventCandidate(
        item=make_item(
            (
                "Сразу три лесных пожара тушат "
                "в Новороссийске"
            ),
            "Wed, 09 Sep 2026 11:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.wildfire,
            "Novorossiysk",
        ),
    )

    third = EventCandidate(
        item=make_item(
            (
                "Пожар на предприятии "
                "в Новороссийске"
            ),
            "Wed, 09 Sep 2026 12:00:00 GMT",
        ),
        classification=make_classification(
            EventCategory.industrial_fire,
            "Novorossiysk",
        ),
    )

    clusters = cluster_event_candidates(
        [
            first,
            second,
            third,
        ]
    )

    cluster_sizes = sorted(
        len(cluster)
        for cluster in clusters
    )

    assert cluster_sizes == [1, 2]
