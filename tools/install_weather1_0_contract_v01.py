from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = REPO_ROOT / "dev-snapshots"
FILES = {'backend/schemas/weather.py': 'from __future__ import annotations\n\nfrom datetime import datetime\nfrom typing import Literal\n\nfrom pydantic import BaseModel, Field\n\n\nWeatherDataKind = Literal[\n    "forecast",\n    "analysis",\n    "reanalysis",\n    "observation",\n]\n\n\nclass WeatherUnits(BaseModel):\n    wind_components: str = "m/s"\n    wind_speed: str = "m/s"\n    wind_direction: str = "degrees_from_north"\n    precipitation_rate: str = "mm/h"\n    precipitation_accumulation: str = "mm"\n\n\nclass WeatherProvenance(BaseModel):\n    provider: str\n    model: str\n    product: str\n    data_kind: WeatherDataKind\n    forecast_reference_time: datetime | None = None\n    valid_time: datetime\n    retrieved_at: datetime\n    source_uri: str | None = None\n    fallback_used: bool = False\n    quality_flags: list[str] = Field(default_factory=list)\n\n\nclass WeatherPoint(BaseModel):\n    latitude: float = Field(ge=-90.0, le=90.0)\n    longitude: float = Field(ge=-180.0, le=180.0)\n\n    wind_u_10m_ms: float\n    wind_v_10m_ms: float\n    wind_speed_10m_ms: float = Field(ge=0.0)\n    wind_from_direction_deg: float = Field(ge=0.0, lt=360.0)\n\n    precipitation_rate_mm_h: float | None = Field(default=None, ge=0.0)\n    precipitation_accumulation_mm: float | None = Field(default=None, ge=0.0)\n    precipitation_interval_start: datetime | None = None\n    precipitation_interval_end: datetime | None = None\n\n    provenance: WeatherProvenance\n    units: WeatherUnits = Field(default_factory=WeatherUnits)\n', 'backend/services/weather_math.py': 'from __future__ import annotations\n\nimport math\n\n\nclass PrecipitationSemanticsError(ValueError):\n    pass\n\n\ndef wind_speed_ms(u_ms: float, v_ms: float) -> float:\n    return math.hypot(float(u_ms), float(v_ms))\n\n\ndef wind_from_direction_deg(u_ms: float, v_ms: float) -> float:\n    u = float(u_ms)\n    v = float(v_ms)\n\n    if math.isclose(u, 0.0, abs_tol=1e-12) and math.isclose(\n        v,\n        0.0,\n        abs_tol=1e-12,\n    ):\n        return 0.0\n\n    return math.degrees(math.atan2(-u, -v)) % 360.0\n\n\ndef wind_components_from_speed_direction(\n    speed_ms: float,\n    direction_from_deg: float,\n) -> tuple[float, float]:\n    speed = float(speed_ms)\n    if speed < 0.0:\n        raise ValueError("wind speed cannot be negative")\n\n    direction = math.radians(float(direction_from_deg) % 360.0)\n    u = -speed * math.sin(direction)\n    v = -speed * math.cos(direction)\n    return u, v\n\n\ndef precipitation_m_to_mm(value_m: float) -> float:\n    value = float(value_m)\n    if value < 0.0:\n        raise ValueError("precipitation accumulation cannot be negative")\n    return value * 1000.0\n\n\ndef deaccumulate_precipitation_mm(\n    *,\n    previous_accumulation_mm: float,\n    current_accumulation_mm: float,\n    interval_hours: float,\n) -> tuple[float, float]:\n    previous = float(previous_accumulation_mm)\n    current = float(current_accumulation_mm)\n    hours = float(interval_hours)\n\n    if previous < 0.0 or current < 0.0:\n        raise ValueError("precipitation accumulation cannot be negative")\n    if hours <= 0.0:\n        raise ValueError("interval_hours must be positive")\n\n    interval = current - previous\n\n    if interval < -1e-9:\n        raise PrecipitationSemanticsError(\n            "accumulated precipitation decreased; possible forecast-cycle reset "\n            "or mixed model runs"\n        )\n\n    interval = max(0.0, interval)\n    return interval, interval / hours\n\n\ndef normalize_longitude_180(longitude_deg: float) -> float:\n    value = float(longitude_deg)\n    return ((value + 180.0) % 360.0) - 180.0\n\n\ndef longitude_for_dataset(\n    longitude_deg: float,\n    *,\n    dataset_uses_360: bool,\n) -> float:\n    lon = normalize_longitude_180(longitude_deg)\n    if dataset_uses_360 and lon < 0.0:\n        return lon + 360.0\n    return lon\n', 'backend/services/weather_provider.py': 'from __future__ import annotations\n\nfrom datetime import datetime\nfrom typing import Protocol, runtime_checkable\n\nfrom backend.schemas.weather import WeatherPoint\n\n\n@runtime_checkable\nclass WeatherProvider(Protocol):\n    provider_name: str\n\n    def get_point(\n        self,\n        *,\n        latitude: float,\n        longitude: float,\n        valid_time: datetime | None = None,\n    ) -> WeatherPoint:\n        ...\n', 'tests/test_weather_math.py': 'import pytest\n\nfrom backend.services.weather_math import (\n    PrecipitationSemanticsError,\n    deaccumulate_precipitation_mm,\n    longitude_for_dataset,\n    precipitation_m_to_mm,\n    wind_components_from_speed_direction,\n    wind_from_direction_deg,\n    wind_speed_ms,\n)\n\n\n@pytest.mark.parametrize(\n    ("u", "v", "expected"),\n    [\n        (0.0, -10.0, 0.0),\n        (-10.0, 0.0, 90.0),\n        (0.0, 10.0, 180.0),\n        (10.0, 0.0, 270.0),\n    ],\n)\ndef test_cardinal_wind_from_direction(u, v, expected):\n    assert wind_from_direction_deg(u, v) == pytest.approx(expected)\n\n\ndef test_wind_speed_uses_vector_magnitude():\n    assert wind_speed_ms(3.0, 4.0) == pytest.approx(5.0)\n\n\n@pytest.mark.parametrize("direction", [0.0, 45.0, 90.0, 180.0, 270.0, 359.0])\ndef test_wind_round_trip(direction):\n    u, v = wind_components_from_speed_direction(12.5, direction)\n    assert wind_speed_ms(u, v) == pytest.approx(12.5)\n    assert wind_from_direction_deg(u, v) == pytest.approx(direction)\n\n\ndef test_precipitation_m_to_mm():\n    assert precipitation_m_to_mm(0.004) == pytest.approx(4.0)\n\n\ndef test_deaccumulation_returns_interval_and_rate():\n    interval, rate = deaccumulate_precipitation_mm(\n        previous_accumulation_mm=4.0,\n        current_accumulation_mm=10.0,\n        interval_hours=3.0,\n    )\n    assert interval == pytest.approx(6.0)\n    assert rate == pytest.approx(2.0)\n\n\ndef test_deaccumulation_rejects_cycle_reset():\n    with pytest.raises(PrecipitationSemanticsError):\n        deaccumulate_precipitation_mm(\n            previous_accumulation_mm=10.0,\n            current_accumulation_mm=2.0,\n            interval_hours=3.0,\n        )\n\n\ndef test_longitude_conversion_for_0_360_dataset():\n    assert longitude_for_dataset(-5.0, dataset_uses_360=True) == pytest.approx(355.0)\n    assert longitude_for_dataset(37.5, dataset_uses_360=True) == pytest.approx(37.5)\n', 'tests/test_weather_schema.py': 'from datetime import datetime, timezone\n\nfrom backend.schemas.weather import WeatherPoint, WeatherProvenance\n\n\ndef test_weather_point_contract():\n    valid_time = datetime(2026, 9, 19, 0, tzinfo=timezone.utc)\n\n    point = WeatherPoint(\n        latitude=44.7,\n        longitude=37.8,\n        wind_u_10m_ms=3.0,\n        wind_v_10m_ms=4.0,\n        wind_speed_10m_ms=5.0,\n        wind_from_direction_deg=216.86989764584402,\n        precipitation_rate_mm_h=1.5,\n        precipitation_accumulation_mm=4.5,\n        precipitation_interval_start=datetime(\n            2026, 9, 18, 21, tzinfo=timezone.utc\n        ),\n        precipitation_interval_end=valid_time,\n        provenance=WeatherProvenance(\n            provider="ecmwf",\n            model="ifs",\n            product="open-data-0p25",\n            data_kind="forecast",\n            forecast_reference_time=datetime(\n                2026, 9, 18, 18, tzinfo=timezone.utc\n            ),\n            valid_time=valid_time,\n            retrieved_at=datetime(\n                2026, 9, 18, 22, tzinfo=timezone.utc\n            ),\n            source_uri="google",\n            fallback_used=False,\n        ),\n    )\n\n    assert point.units.wind_components == "m/s"\n    assert point.units.precipitation_rate == "mm/h"\n    assert point.provenance.data_kind == "forecast"\n    assert point.wind_speed_10m_ms == 5.0\n'}


def backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"{path.name}.before_weather1_0_{stamp}"
    shutil.copy2(path, target)
    return target


def main() -> int:
    backups = []

    for relative, content in FILES.items():
        path = REPO_ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing == content:
                continue
            backups.append(backup(path))

        path.write_text(content, encoding="utf-8")

    print("WEATHER-1.0 Canonical Weather Contract v0.1 installed.")
    print("Created/updated:")
    for relative in FILES:
        print(f"  {relative}")

    if backups:
        print("Backups:")
        for path in backups:
            print(f"  {path.relative_to(REPO_ROOT)}")

    print("No API, OpenDrift, OpenOil, or frontend files were modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
