from agents.news_agent.event_lifecycle import (
    detect_lifecycle_status,
)


def test_active_fire():
    result = detect_lifecycle_status(
        "Пожар продолжается, работают службы"
    )

    assert result.status == "active"


def test_active_tushat():
    result = detect_lifecycle_status(
        "Три лесных пожара тушат в Новороссийске"
    )

    assert result.status == "active"


def test_active_tushenie():
    result = detect_lifecycle_status(
        "В тушении пожара задействована авиация"
    )

    assert result.status == "active"


def test_active_future_response_is_not_resolved():
    result = detect_lifecycle_status(
        "Власти планируют потушить пожар "
        "в ближайшие часы"
    )

    assert result.status == "active"


def test_contained_fire():
    result = detect_lifecycle_status(
        "Пожар локализован"
    )

    assert result.status == "contained"


def test_contained_plural_form():
    result = detect_lifecycle_status(
        "Очаги локализованы"
    )

    assert result.status == "contained"


def test_contained_under_control():
    result = detect_lifecycle_status(
        "Пожар взят под контроль"
    )

    assert result.status == "contained"


def test_resolved_fire():
    result = detect_lifecycle_status(
        "Пожар ликвидирован"
    )

    assert result.status == "resolved"


def test_resolved_potushili():
    result = detect_lifecycle_status(
        "В Новороссийске потушили лесной пожар"
    )

    assert result.status == "resolved"


def test_resolved_likvidirovali():
    result = detect_lifecycle_status(
        "Спасатели ликвидировали пожар"
    )

    assert result.status == "resolved"


def test_resolved_restored_power():
    result = detect_lifecycle_status(
        "Электроснабжение восстановили "
        "после пожара на подстанции"
    )

    assert result.status == "resolved"


def test_resolved_english_extinguished():
    result = detect_lifecycle_status(
        "Wildfire near Novorossiysk was extinguished"
    )

    assert result.status == "resolved"


def test_contained_wins_over_active():
    result = detect_lifecycle_status(
        "Пожар локализован, тушение продолжается"
    )

    assert result.status == "contained"


def test_resolved_wins_over_active():
    result = detect_lifecycle_status(
        "Пожар потушен, пожарные продолжают "
        "работать на месте"
    )

    assert result.status == "resolved"


def test_default_detected():
    result = detect_lifecycle_status(
        "На территории обнаружен пожар"
    )

    assert result.status == "detected"



def test_active_plans_to_extinguish_russian():
    result = detect_lifecycle_status(
        "Власти заявили о планах потушить "
        "пожар на подстанции"
    )

    assert result.status == "active"


def test_active_plans_to_extinguish_english():
    result = detect_lifecycle_status(
        "Authorities plan to extinguish "
        "the fire in the coming hours"
    )

    assert result.status == "active"
