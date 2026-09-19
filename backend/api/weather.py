from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.schemas.weather import WeatherPoint
from backend.services.ecmwf_weather_provider import (
    EcmwfOpenDataWeatherProvider,
    WeatherProviderError,
    WeatherSourceUnavailable,
    WeatherTimeUnavailable,
)
from backend.services.weather_provider import WeatherProvider


router = APIRouter(
    prefix="/weather",
    tags=["weather"],
)


@lru_cache(maxsize=1)
def get_weather_provider() -> WeatherProvider:
    """
    Return the process-wide operational weather provider.

    The provider keeps only configuration in memory. GRIB assets are cached
    on disk by the ECMWF implementation.
    """
    return EcmwfOpenDataWeatherProvider()


@router.get(
    "/point",
    response_model=WeatherPoint,
    summary="Operational weather at a point",
)
def get_weather_point(
    latitude: Annotated[
        float,
        Query(
            ge=-90.0,
            le=90.0,
            description="Latitude in decimal degrees.",
        ),
    ],
    longitude: Annotated[
        float,
        Query(
            ge=-180.0,
            le=180.0,
            description="Longitude in decimal degrees.",
        ),
    ],
    valid_time: Annotated[
        datetime | None,
        Query(
            description=(
                "Requested UTC-valid time. WEATHER-1.2 currently snaps "
                "forward to the next available ECMWF model step; the actual "
                "time used is returned in provenance.valid_time."
            ),
        ),
    ] = None,
    provider: WeatherProvider = Depends(get_weather_provider),
) -> WeatherPoint:
    try:
        return provider.get_point(
            latitude=latitude,
            longitude=longitude,
            valid_time=valid_time,
        )
    except WeatherTimeUnavailable as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except WeatherSourceUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
