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



def _matches_satellite_filters(
    observation,
    *,
    observation_type=None,
    derivation_level=None,
    source_image_id=None,
):
    if (
        observation_type is not None
        and observation.get("observation_type")
        != observation_type
    ):
        return False

    if (
        derivation_level is not None
        and observation.get("derivation_level")
        != derivation_level
    ):
        return False

    if (
        source_image_id is not None
        and observation.get("source_image_id")
        != source_image_id
    ):
        return False

    return True


@router.get("/")
def get_satellite_observations(
    observation_type: str | None = None,
    derivation_level: str | None = None,
    source_image_id: str | None = None,
    store: EventStore = Depends(
        get_satellite_observation_store
    ),
):
    observations = store.list_satellite_observations()

    return [
        observation
        for observation in observations
        if _matches_satellite_filters(
            observation,
            observation_type=observation_type,
            derivation_level=derivation_level,
            source_image_id=source_image_id,
        )
    ]


@router.get("/candidates.geojson")
def get_satellite_candidate_geojson(
    source_image_id: str | None = None,
    store: EventStore = Depends(
        get_satellite_observation_store
    ),
):
    observations = store.list_satellite_observations()
    features = []

    for observation in observations:
        if observation.get(
            "observation_type"
        ) != "sar_dark_spot_candidate":
            continue

        if observation.get(
            "derivation_level"
        ) != "derived":
            continue

        if (
            source_image_id is not None
            and observation.get("source_image_id")
            != source_image_id
        ):
            continue

        geometry = observation.get("geometry")

        if not isinstance(geometry, dict):
            continue

        provenance = observation.get(
            "provenance"
        ) or {}

        features.append(
            {
                "type": "Feature",
                "id": observation.get("id"),
                "geometry": geometry,
                "properties": {
                    "observation_id": observation.get(
                        "id"
                    ),
                    "information_type": observation.get(
                        "information_type"
                    ),
                    "derivation_level": observation.get(
                        "derivation_level"
                    ),
                    "observation_type": observation.get(
                        "observation_type"
                    ),
                    "source_image_id": observation.get(
                        "source_image_id"
                    ),
                    "acquisition_time": observation.get(
                        "acquisition_time"
                    ),
                    "review_status": observation.get(
                        "review_status"
                    ),
                    "confidence": observation.get(
                        "confidence"
                    ),
                    "processing_version": observation.get(
                        "processing_version"
                    ),
                    "candidate_id": provenance.get(
                        "candidate_id"
                    ),
                    "area_km2": provenance.get(
                        "area_km2"
                    ),
                    "mean_vv_db": provenance.get(
                        "mean_vv_db"
                    ),
                    "threshold_db": provenance.get(
                        "threshold_db"
                    ),
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "semantics": {
            "information_type": "satellite_observation",
            "observation_type": "sar_dark_spot_candidate",
            "does_not_mean": [
                "oil_spill",
                "confirmed_pollution",
                "confirmed_event",
                "causal_link_to_event",
            ],
        },
    }


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
