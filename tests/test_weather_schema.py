from datetime import datetime, timezone

from backend.schemas.weather import WeatherPoint, WeatherProvenance


def test_weather_point_contract():
    valid_time = datetime(2026, 9, 19, 0, tzinfo=timezone.utc)

    point = WeatherPoint(
        latitude=44.7,
        longitude=37.8,
        wind_u_10m_ms=3.0,
        wind_v_10m_ms=4.0,
        wind_speed_10m_ms=5.0,
        wind_from_direction_deg=216.86989764584402,
        precipitation_rate_mm_h=1.5,
        precipitation_accumulation_mm=4.5,
        precipitation_interval_start=datetime(
            2026, 9, 18, 21, tzinfo=timezone.utc
        ),
        precipitation_interval_end=valid_time,
        provenance=WeatherProvenance(
            provider="ecmwf",
            model="ifs",
            product="open-data-0p25",
            data_kind="forecast",
            forecast_reference_time=datetime(
                2026, 9, 18, 18, tzinfo=timezone.utc
            ),
            valid_time=valid_time,
            retrieved_at=datetime(
                2026, 9, 18, 22, tzinfo=timezone.utc
            ),
            source_uri="google",
            fallback_used=False,
        ),
    )

    assert point.units.wind_components == "m/s"
    assert point.units.precipitation_rate == "mm/h"
    assert point.provenance.data_kind == "forecast"
    assert point.wind_speed_10m_ms == 5.0
