from agents.news_agent.models import NewsItem

from agents.news_agent.rule_classifier import (
    classify_news_item,
)

from agents.news_agent.classification import (
    NewsClassificationType,
)

from backend.models.event import (
    EventCategory,
)


def make_item(
    title: str
) -> NewsItem:

    return NewsItem(
        title=title,
        url="https://example.com",
        source="Test Source",
        published_at=(
            "Thu, 10 Sep 2026 "
            "07:00:00 GMT"
        ),
        summary=None,
    )


def test_russian_wildfire():

    item = make_item(
        "Сразу три лесных пожара "
        "тушат в Новороссийске"
    )

    result = classify_news_item(
        item
    )

    assert (
        result.classification
        == NewsClassificationType.incident
    )

    assert (
        result.category
        == EventCategory.wildfire
    )


def test_extinguished_wildfire_is_follow_up():

    item = make_item(
        "Лесной пожар возле хутора Дюрсо "
        "под Новороссийском ликвидирован"
    )

    result = classify_news_item(
        item
    )

    assert (
        result.classification
        == NewsClassificationType.follow_up
    )

    assert (
        result.category
        == EventCategory.wildfire
    )


def test_mazut_terminal_fire_is_industrial():

    item = make_item(
        "Новороссийск атаковали беспилотники, "
        "сообщается о пожаре "
        "на мазутном терминале"
    )

    result = classify_news_item(
        item
    )

    assert (
        result.classification
        == NewsClassificationType.incident
    )

    assert (
        result.category
        == EventCategory.industrial_fire
    )


def test_residential_fire_is_noise():

    item = make_item(
        "Мужчина и женщина погибли "
        "при пожаре в доме"
    )

    result = classify_news_item(
        item
    )

    assert (
        result.classification
        == NewsClassificationType.noise
    )