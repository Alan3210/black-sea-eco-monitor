from backend.api.ground_stations import router as ground_stations_router

from fastapi import FastAPI

from backend.api.wind_field import router as wind_field_router
from backend.api.air_field import router as air_field_router
from backend.api.geos_cf_field import router as geos_cf_field_router
from backend.api.air_model_crosscheck import router as air_model_crosscheck_router
from backend.api.satellite_air_field import router as satellite_air_field_router

from backend.api.impact import router as impact_router
from backend.api.impact_registry import router as impact_registry_router
from backend.api.weather import router as weather_router
from backend.api.ar_scene import router as ar_scene_router
from backend.api.ocean_drift import router as ocean_drift_router
from backend.api.ocean_currents import router as ocean_currents_router
from backend.api.evidence import router as evidence_router
from backend.api.events import router as events_router
from backend.api.monitor_events import (
    router as monitor_events_router,
)

from backend.api.satellite_observations import (
    router as satellite_observations_router,
)

from backend.api.monitor_dashboard import (
    router as monitor_dashboard_router,
)

from backend.database.database import engine, Base
from backend.database import models

from backend.config import settings


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0"
)


app.include_router(
    events_router,
    prefix="/events"
)

app.include_router(
    impact_registry_router
)

app.include_router(
    weather_router
)

app.include_router(
    evidence_router,
    prefix="/events"
)


app.include_router(
    monitor_events_router,
    prefix="/monitor/events",
    tags=["monitor"],
)


app.include_router(
    ocean_currents_router
)


app.include_router(
    ocean_drift_router
)


app.include_router(
    ar_scene_router
)





app.include_router(
    impact_router
)


app.include_router(
    satellite_observations_router,
    prefix="/satellite/observations",
    tags=["satellite"],
)



app.include_router(
    monitor_dashboard_router,
    prefix="/monitor/dashboard",
    tags=["monitor"],
)


app.include_router(
    wind_field_router
)


@app.get("/")
def root():

    return {
        "project": settings.PROJECT_NAME,
        "status": "running"
    }

app.include_router(air_field_router)
app.include_router(geos_cf_field_router)
app.include_router(air_model_crosscheck_router)
app.include_router(satellite_air_field_router)

app.include_router(ground_stations_router)
