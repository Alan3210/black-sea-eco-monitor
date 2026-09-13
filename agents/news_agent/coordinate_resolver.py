from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedCoordinates:
    latitude: float
    longitude: float
    precision: str = "canonical_location"


# Static coordinates for the canonical locations that are
# currently produced by Location Resolver.
#
# Important:
# These are representative map points for the canonical
# location, not exact incident coordinates.
LOCATION_COORDINATES = {
    "Novorossiysk": ResolvedCoordinates(
        latitude=44.7240,
        longitude=37.7691,
    ),
    "Gelendzhik": ResolvedCoordinates(
        latitude=44.5609,
        longitude=38.0767,
    ),
    "Anapa": ResolvedCoordinates(
        latitude=44.8943,
        longitude=37.3169,
    ),
    "Sochi": ResolvedCoordinates(
        latitude=43.5855,
        longitude=39.7231,
    ),
    "Sevastopol": ResolvedCoordinates(
        latitude=44.6054,
        longitude=33.5221,
    ),
    "Utrish Reserve": ResolvedCoordinates(
        latitude=44.7605,
        longitude=37.3854,
    ),
}


def resolve_coordinates(
    location_name: str | None,
) -> ResolvedCoordinates | None:
    if not location_name:
        return None

    normalized = location_name.strip()

    if not normalized:
        return None

    return LOCATION_COORDINATES.get(
        normalized
    )
