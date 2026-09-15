from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from agents.ocean_data.drift_forecast import (
    DEFAULT_DIFFUSIVITY_M2_S,
    DEFAULT_HOURS,
    DEFAULT_PARTICLES,
    DEFAULT_RADIUS_M,
    MAX_DIFFUSIVITY_M2_S,
    MAX_PARTICLES,
    MAX_RADIUS_M,
    MIN_PARTICLES,
    OceanDriftError,
    OceanDriftInputError,
    STANDARD_HORIZONS_HOURS,
    run_surface_drift,
)


router = APIRouter(
    prefix="/ocean/drift",
    tags=["ocean"],
)


@router.get("/")
def get_drift_forecast(
    lon: float = Query(
        ...,
        description=(
            "Release longitude in decimal degrees."
        ),
    ),
    lat: float = Query(
        ...,
        description=(
            "Release latitude in decimal degrees."
        ),
    ),
    at: str | None = Query(
        default=None,
        description=(
            "UTC release time in ISO 8601. "
            "Rounded down to the nearest model hour."
        ),
    ),
    hours: int = Query(
        default=DEFAULT_HOURS,
        description=(
            "Forecast horizon. Supported values: "
            + ", ".join(
                str(value)
                for value in STANDARD_HORIZONS_HOURS
            )
            + "."
        ),
    ),
    particles: int = Query(
        default=DEFAULT_PARTICLES,
        ge=MIN_PARTICLES,
        le=MAX_PARTICLES,
        description=(
            "Number of passive tracer particles."
        ),
    ),
    radius_m: float = Query(
        default=DEFAULT_RADIUS_M,
        ge=0,
        le=MAX_RADIUS_M,
        description=(
            "OpenDrift Gaussian seeding radius in metres."
        ),
    ),
    diffusivity_m2_s: float = Query(
        default=DEFAULT_DIFFUSIVITY_M2_S,
        ge=0,
        le=MAX_DIFFUSIVITY_M2_S,
        description=(
            "Constant horizontal diffusivity in m2/s."
        ),
    ),
):
    try:
        return run_surface_drift(
            longitude=lon,
            latitude=lat,
            at=at,
            hours=hours,
            particles=particles,
            radius_m=radius_m,
            diffusivity_m2_s=diffusivity_m2_s,
        )
    except OceanDriftInputError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except OceanDriftError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
