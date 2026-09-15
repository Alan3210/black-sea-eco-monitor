from fastapi import APIRouter, HTTPException, Query

from agents.ocean_data.copernicus_currents import (
    DEFAULT_STRIDE,
    OceanCurrentsError,
    OceanCurrentsInputError,
    get_surface_currents,
)


router = APIRouter(
    prefix="/ocean/currents",
    tags=["ocean"],
)


@router.get("/")
def get_currents(
    at: str | None = Query(
        default=None,
        description=(
            "Requested UTC time in ISO 8601. "
            "Rounded down to the nearest hour."
        ),
    ),
    stride: int = Query(
        default=DEFAULT_STRIDE,
        ge=1,
        le=40,
        description=(
            "Display decimation. 8 means one vector "
            "every ~0.2 degrees."
        ),
    ),
):
    try:
        return get_surface_currents(
            at=at,
            stride=stride,
        )
    except OceanCurrentsInputError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except OceanCurrentsError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
