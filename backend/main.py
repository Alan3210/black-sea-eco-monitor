from fastapi import FastAPI

from api.events import router as events_router

from database.database import engine, Base
from database import models

app = FastAPI(
    title="Black Sea Eco Monitor API",
    version="0.1.0"
)

Base.metadata.create_all(
    bind=engine
)

app.include_router(
    events_router,
    prefix="/events"
)


@app.get("/")
def root():

    return {
        "project":
        "Black Sea Eco Monitor",

        "status":
        "running"
    }