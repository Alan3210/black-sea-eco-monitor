from fastapi import APIRouter
from backend.services.ground_station_service import (
    get_station_sources,
    get_station_observations,
)

router = APIRouter(prefix="/air", tags=["air"])

@router.get("/stations/sources")
def stations_sources():
    return {"sources": get_station_sources()}

@router.get("/stations")
def stations():
    return get_station_observations()
