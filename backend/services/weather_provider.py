from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from backend.schemas.weather import WeatherPoint


@runtime_checkable
class WeatherProvider(Protocol):
    provider_name: str

    def get_point(
        self,
        *,
        latitude: float,
        longitude: float,
        valid_time: datetime | None = None,
    ) -> WeatherPoint:
        ...
