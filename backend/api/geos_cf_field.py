from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.services.geos_cf_field import fetch_geos_cf_field
from backend.services.geos_cf_provider import GeosCFError


router = APIRouter(prefix="/air", tags=["air"])


@router.get("/geos-cf-field")
def get_geos_cf_field(
    product: str = Query(
        default="pm25",
        description="GEOS-CF product: pm25, pm10, no2, so2, o3, co",
    ),
    time_index: int = Query(
        default=0,
        ge=0,
        le=119,
        description=(
            "Hourly GEOS-CF field index in the latest 120-step forecast."
        ),
    ),
    stride: int = Query(
        default=1,
        ge=1,
        le=8,
        description=(
            "Return every Nth native grid cell. "
            "No interpolation is performed."
        ),
    ),
):
    try:
        return fetch_geos_cf_field(
            product=product,
            time_index=time_index,
            stride=stride,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GeosCFError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"GEOS-CF field failed: {exc}",
        ) from exc
