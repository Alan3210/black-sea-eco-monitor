from fastapi import FastAPI

from backend.api.evidence import router as evidence_router

from backend.api.events import router as events_router

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
    evidence_router,
    prefix="/events"
)

@app.get("/")
def root():

    return {
        "project": settings.PROJECT_NAME,
        "status": "running"
    }