from agents.news_agent.coordinate_resolver import (
    resolve_coordinates,
)


def test_novorossiysk_coordinates():
    result = resolve_coordinates(
        "Novorossiysk"
    )

    assert result is not None
    assert result.latitude == 44.7240
    assert result.longitude == 37.7691


def test_gelendzhik_coordinates():
    result = resolve_coordinates(
        "Gelendzhik"
    )

    assert result is not None
    assert result.latitude == 44.5609
    assert result.longitude == 38.0767


def test_anapa_coordinates():
    result = resolve_coordinates(
        "Anapa"
    )

    assert result is not None
    assert result.latitude == 44.8943
    assert result.longitude == 37.3169


def test_sochi_coordinates():
    result = resolve_coordinates(
        "Sochi"
    )

    assert result is not None
    assert result.latitude == 43.5855
    assert result.longitude == 39.7231


def test_sevastopol_coordinates():
    result = resolve_coordinates(
        "Sevastopol"
    )

    assert result is not None
    assert result.latitude == 44.6054
    assert result.longitude == 33.5221


def test_utrish_coordinates():
    result = resolve_coordinates(
        "Utrish Reserve"
    )

    assert result is not None
    assert result.latitude == 44.7605
    assert result.longitude == 37.3854


def test_unknown_location_returns_none():
    result = resolve_coordinates(
        "Unknown Place"
    )

    assert result is None


def test_empty_location_returns_none():
    assert resolve_coordinates(None) is None
    assert resolve_coordinates("") is None
    assert resolve_coordinates("   ") is None
