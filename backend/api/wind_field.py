from __future__ import annotations

from functools import lru_cache

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from backend.services.ecmwf_weather_provider import (
    WeatherProviderError,
    WeatherSourceUnavailable,
    WeatherTimeUnavailable,
)
from backend.services.wind_field import (
    DEFAULT_WIND_FIELD_STRIDE,
    MAX_WIND_FIELD_STRIDE,
    MIN_WIND_FIELD_STRIDE,
    EcmwfWindFieldService,
)


router = APIRouter(
    prefix="/weather",
    tags=["weather"],
)


@lru_cache(maxsize=1)
def get_wind_field_service() -> EcmwfWindFieldService:
    return EcmwfWindFieldService()


@router.get("/wind-field")
def get_wind_field(
    at: str | None = Query(
        default=None,
        description=(
            "Requested UTC valid time in ISO 8601. "
            "The ECMWF 10 m wind field is linearly "
            "interpolated between native IFS forecast steps."
        ),
    ),
    stride: int = Query(
        default=DEFAULT_WIND_FIELD_STRIDE,
        ge=MIN_WIND_FIELD_STRIDE,
        le=MAX_WIND_FIELD_STRIDE,
        description=(
            "Spatial decimation of the native 0.25 degree "
            "ECMWF grid."
        ),
    ),
    service: EcmwfWindFieldService = Depends(
        get_wind_field_service
    ),
):
    try:
        return service.get_field(
            at=at,
            stride=stride,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except WeatherTimeUnavailable as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except (
        WeatherSourceUnavailable,
        WeatherProviderError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
