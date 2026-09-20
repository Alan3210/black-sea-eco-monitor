from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from backend.services.cams_air_field import (
    CamsAirFieldError,
    CamsAirFieldService,
)
from backend.services.cams_air_quality_provider import (
    CamsAirQualityError,
    CamsRequestError,
)


router = APIRouter()


@lru_cache(maxsize=1)
def get_air_field_service():
    return CamsAirFieldService()


@router.get("/air/field")
def air_field(
    pollutant: str = Query(
        default="pm25",
    ),
    run_date: str | None = Query(
        default=None,
        description="CAMS forecast run date YYYY-MM-DD",
    ),
    lead_hour: int | None = Query(
        default=None,
        ge=0,
        le=96,
    ),
    stride: int = Query(
        default=2,
        ge=1,
        le=8,
    ),
):
    try:
        return (
            get_air_field_service()
            .get_field(
                pollutant=pollutant,
                run_date=run_date,
                lead_hour=lead_hour,
                stride=stride,
            )
        )
    except (
        CamsRequestError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except (
        CamsAirFieldError,
        CamsAirQualityError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
