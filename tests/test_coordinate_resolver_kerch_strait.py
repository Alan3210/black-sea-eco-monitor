from agents.news_agent.coordinate_resolver import (
    resolve_coordinates,
)


def test_resolves_kerch_strait_to_canonical_map_point():
    result = resolve_coordinates(
        "Kerch Strait"
    )

    assert result is not None
    assert result.latitude == 45.3
    assert result.longitude == 36.5
    assert (
        result.precision
        == "canonical_location"
    )


def test_kerch_strait_coordinate_is_representative_not_exact():
    result = resolve_coordinates(
        "Kerch Strait"
    )

    assert result is not None
    assert (
        result.precision
        == "canonical_location"
    )
