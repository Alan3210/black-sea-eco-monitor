from datetime import datetime, timedelta, timezone

from agents.news_agent.event_matcher import (
    calculate_event_match,
)


def test_same_wildfire_matches():

    result = calculate_event_match(
        existing_title=(
            "Лесной пожар под Новороссийском"
        ),
        new_title=(
            "Три лесных пожара тушат под Новороссийском"
        ),
        existing_category="wildfire",
        new_category="wildfire",
        existing_location="Novorossiysk",
        new_location="Novorossiysk",
    )

    assert result.is_match is True


def test_different_categories_do_not_match():

    result = calculate_event_match(
        existing_title="Пожар в лесу",
        new_title="Пожар на терминале",
        existing_category="wildfire",
        new_category="industrial_fire",
        existing_location="Novorossiysk",
        new_location="Novorossiysk",
    )

    assert result.is_match is False


def test_same_city_different_time_events_do_not_match():

    result = calculate_event_match(
        existing_title="Лесной пожар у Дюрсо",
        new_title="Лесной пожар у Дюрсо",
        existing_category="wildfire",
        new_category="wildfire",
        existing_location="Novorossiysk",
        new_location="Novorossiysk",
        existing_time=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
        new_time=datetime(
            2026,
            10,
            1,
            tzinfo=timezone.utc,
        ),
    )

    assert result.is_match is False
