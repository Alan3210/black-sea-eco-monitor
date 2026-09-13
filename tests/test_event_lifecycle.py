from agents.news_agent.event_lifecycle import (
    detect_lifecycle_status,
)


def test_active_fire():

    result = detect_lifecycle_status(
        "Пожар продолжается, работают службы"
    )

    assert result.status == "active"


def test_contained_fire():

    result = detect_lifecycle_status(
        "Пожар локализован"
    )

    assert result.status == "contained"


def test_resolved_fire():

    result = detect_lifecycle_status(
        "Пожар ликвидирован"
    )

    assert result.status == "resolved"


def test_default_detected():

    result = detect_lifecycle_status(
        "На территории обнаружен пожар"
    )

    assert result.status == "detected"
