from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from backend.services.sentinel5p_provider import Sentinel5PError
from backend.services.sentinel5p_satellite_field import (
    DEFAULT_MAX_LOOKBACK_DAYS,
    Sentinel5PNoCoverageError,
    fetch_satellite_field,
)


router = APIRouter(prefix="/air", tags=["air"])


@router.get("/satellite-field")
def get_satellite_field(
    product: str = Query(
        default="no2",
        description=(
            "Sentinel-5P/TROPOMI L2 product: no2, so2, co, o3, ch4, "
            "hcho, aer_ai_340_380, aer_ai_354_388"
        ),
    ),
    date_: date | None = Query(
        default=None,
        alias="date",
        description=(
            "Exact UTC observation day. If omitted, the API searches "
            "backward for the latest day with valid TROPOMI pixels."
        ),
    ),
    timeliness: Literal["NRTI", "OFFL", "RPRO"] = Query(
        default="NRTI",
        description="Sentinel-5P processing timeliness.",
    ),
    stride: int = Query(
        default=1,
        ge=1,
        le=8,
        description="Return every Nth pixel. No interpolation is performed.",
    ),
    lookback_days: int = Query(
        default=DEFAULT_MAX_LOOKBACK_DAYS,
        ge=0,
        le=14,
        description=(
            "Only used when date is omitted. Maximum number of previous "
            "UTC days searched for non-empty satellite coverage."
        ),
    ),
):
    try:
        return fetch_satellite_field(
            product=product,
            day=date_,
            timeliness=timeliness,
            stride=stride,
            max_lookback_days=lookback_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Sentinel5PNoCoverageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Sentinel5PError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Sentinel-5P satellite field failed: {exc}",
        ) from exc
