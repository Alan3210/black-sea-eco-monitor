from fastapi import FastAPI

from api.events import router as events_router


app = FastAPI(
    title="Black Sea Eco Monitor API",
    version="0.1.0"
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