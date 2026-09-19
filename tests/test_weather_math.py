import pytest

from backend.services.weather_math import (
    PrecipitationSemanticsError,
    deaccumulate_precipitation_mm,
    longitude_for_dataset,
    precipitation_m_to_mm,
    wind_components_from_speed_direction,
    wind_from_direction_deg,
    wind_speed_ms,
)


@pytest.mark.parametrize(
    ("u", "v", "expected"),
    [
        (0.0, -10.0, 0.0),
        (-10.0, 0.0, 90.0),
        (0.0, 10.0, 180.0),
        (10.0, 0.0, 270.0),
    ],
)
def test_cardinal_wind_from_direction(u, v, expected):
    assert wind_from_direction_deg(u, v) == pytest.approx(expected)


def test_wind_speed_uses_vector_magnitude():
    assert wind_speed_ms(3.0, 4.0) == pytest.approx(5.0)


@pytest.mark.parametrize("direction", [0.0, 45.0, 90.0, 180.0, 270.0, 359.0])
def test_wind_round_trip(direction):
    u, v = wind_components_from_speed_direction(12.5, direction)
    assert wind_speed_ms(u, v) == pytest.approx(12.5)
    assert wind_from_direction_deg(u, v) == pytest.approx(direction)


def test_precipitation_m_to_mm():
    assert precipitation_m_to_mm(0.004) == pytest.approx(4.0)


def test_deaccumulation_returns_interval_and_rate():
    interval, rate = deaccumulate_precipitation_mm(
        previous_accumulation_mm=4.0,
        current_accumulation_mm=10.0,
        interval_hours=3.0,
    )
    assert interval == pytest.approx(6.0)
    assert rate == pytest.approx(2.0)


def test_deaccumulation_rejects_cycle_reset():
    with pytest.raises(PrecipitationSemanticsError):
        deaccumulate_precipitation_mm(
            previous_accumulation_mm=10.0,
            current_accumulation_mm=2.0,
            interval_hours=3.0,
        )


def test_longitude_conversion_for_0_360_dataset():
    assert longitude_for_dataset(-5.0, dataset_uses_360=True) == pytest.approx(355.0)
    assert longitude_for_dataset(37.5, dataset_uses_360=True) == pytest.approx(37.5)
