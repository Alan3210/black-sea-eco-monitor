from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from agents.news_agent.event_store import (
    EventStore,
)


router = APIRouter()


def get_satellite_observation_store():
    return EventStore()


@router.get("/")
def get_satellite_observations(
    store: EventStore = Depends(
        get_satellite_observation_store
    ),
):
    return store.list_satellite_observations()


@router.get("/{observation_id}")
def get_satellite_observation(
    observation_id: str,
    store: EventStore = Depends(
        get_satellite_observation_store
    ),
):
    observation = store.get_satellite_observation(
        observation_id
    )

    if observation is None:
        raise HTTPException(
            status_code=404,
            detail="Satellite observation not found",
        )

    return observation
