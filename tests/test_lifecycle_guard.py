from backend.models.event import (
    EventCategory,
)

from agents.news_agent.classification import (
    NewsClassification,
    NewsClassificationType,
)

from agents.news_agent.lifecycle_guard import (
    apply_lifecycle_guard,
)

from agents.news_agent.models import (
    NewsItem,
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


def make_incident():

    return NewsClassification(
        classification=(
            NewsClassificationType.incident
        ),

        category=EventCategory.wildfire,

        location_name="Novorossiysk",

        is_black_sea_region=True,

        confidence=0.9,

        is_new_event=True,

        event_date=None,

        reason="LLM classified this as an incident.",
    )


def test_put_out_fire_becomes_follow_up():

    item = make_item(
        "Лесной пожар возле хутора Дюрсо "
        "под Новороссийском ликвидирован"
    )

    result = apply_lifecycle_guard(
        item,
        make_incident(),
    )

    assert (
        result.classification
        == NewsClassificationType.follow_up
    )

    assert result.is_new_event is False


def test_localized_fire_becomes_follow_up():

    item = make_item(
        "Пожар в лесном массиве "
        "Большого Утриша локализован"
    )

    result = apply_lifecycle_guard(
        item,
        make_incident(),
    )

    assert (
        result.classification
        == NewsClassificationType.follow_up
    )

    assert result.is_new_event is False


def test_extinguished_fire_becomes_follow_up():

    item = make_item(
        "Лесной пожар в Новороссийске потушен"
    )

    result = apply_lifecycle_guard(
        item,
        make_incident(),
    )

    assert (
        result.classification
        == NewsClassificationType.follow_up
    )

    assert result.is_new_event is False


def test_no_pollution_becomes_clear():

    item = make_item(
        "На побережье Черного моря "
        "загрязнение не выявлено"
    )

    classification = NewsClassification(
        classification=(
            NewsClassificationType.incident
        ),

        category=(
            EventCategory.water_pollution
        ),

        location_name="Black Sea",

        is_black_sea_region=True,

        confidence=0.9,

        is_new_event=True,

        event_date=None,

        reason="LLM result.",
    )

    result = apply_lifecycle_guard(
        item,
        classification,
    )

    assert (
        result.classification
        == NewsClassificationType.clear
    )

    assert result.is_new_event is False


def test_active_wildfire_is_not_changed():

    item = make_item(
        "Сразу три лесных пожара "
        "тушат в Новороссийске"
    )

    original = make_incident()

    result = apply_lifecycle_guard(
        item,
        original,
    )

    assert (
        result.classification
        == NewsClassificationType.incident
    )

    assert result.is_new_event is True

def test_active_firefighting_stays_incident():

    item = make_item(
        "Сразу три лесных пожара тушат "
        "в Новороссийске"
    )

    result = apply_lifecycle_guard(
        item,
        make_incident(),
    )

    assert (
        result.classification
        == NewsClassificationType.incident
    )

    assert result.is_new_event is True


def test_liquidated_fire_becomes_follow_up():

    item = make_item(
        "Лесной пожар возле хутора Дюрсо "
        "ликвидирован"
    )

    result = apply_lifecycle_guard(
        item,
        make_incident(),
    )

    assert (
        result.classification
        == NewsClassificationType.follow_up
    )

    assert result.is_new_event is False