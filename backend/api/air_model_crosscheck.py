from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.services.air_model_crosscheck import (
    AirModelCrosscheckError,
    AirModelCrosscheckUnavailable,
    fetch_time_aligned_crosscheck,
)
from backend.services.cams_air_field import CamsAirFieldError
from backend.services.cams_air_quality_provider import CamsAirQualityError
from backend.services.geos_cf_provider import GeosCFError


router = APIRouter(prefix="/air", tags=["air"])


@router.get("/model-crosscheck")
def model_crosscheck(
    product: str = Query(
        default="pm25",
        description="Cross-check product: pm25 or pm10.",
    ),
    geos_time_index: int = Query(
        default=0,
        ge=0,
        le=119,
    ),
    geos_stride: int = Query(
        default=1,
        ge=1,
        le=8,
    ),
    cams_stride: int = Query(
        default=1,
        ge=1,
        le=8,
    ),
    max_time_gap_minutes: float = Query(
        default=45.0,
        ge=0.0,
        le=180.0,
        description=(
            "Maximum allowed absolute valid-time difference between models."
        ),
    ),
):
    try:
        return fetch_time_aligned_crosscheck(
            product=product,
            geos_time_index=geos_time_index,
            geos_stride=geos_stride,
            cams_stride=cams_stride,
            max_time_gap_minutes=max_time_gap_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AirModelCrosscheckUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (
        AirModelCrosscheckError,
        CamsAirFieldError,
        CamsAirQualityError,
        GeosCFError,
    ) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Air model cross-check failed: {exc}",
        ) from exc
