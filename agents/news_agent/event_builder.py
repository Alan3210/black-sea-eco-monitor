from datetime import datetime, timezone
import uuid


from agents.news_agent.models import NewsItem

from agents.news_agent.classification import (
    NewsClassification,
)

from agents.news_agent.coordinate_resolver import (
    resolve_coordinates,
)

from backend.models.event import (
    EnvironmentalEvent,
    Location,
    EventSeverity,
)

from backend.models.evidence import Evidence

from backend.models.source import Source



def estimate_severity(
    classification: NewsClassification
) -> EventSeverity:

    if classification.confidence >= 0.9:

        return EventSeverity.high


    if classification.confidence >= 0.75:

        return EventSeverity.medium


    return EventSeverity.low



def build_event_location(
    location_name: str | None,
) -> Location:

    coordinates = resolve_coordinates(
        location_name
    )

    if coordinates is None:

        return Location(
            latitude=0.0,
            longitude=0.0,
        )

    return Location(
        latitude=coordinates.latitude,
        longitude=coordinates.longitude,
    )



def build_environmental_event(
    item: NewsItem,
    classification: NewsClassification,
) -> EnvironmentalEvent:


    event_id = (
        "news_"
        + str(uuid.uuid4())
    )


    source = Source(

        type="news",

        name=item.source,

        url=item.url,

        reliability=0.7
    )


    evidence = Evidence(

        type="news_report",

        description=item.title,

        confidence=classification.confidence,

        source=source
    )


    return EnvironmentalEvent(

        id=event_id,

        category=classification.category,

        location=build_event_location(
            classification.location_name
        ),

        timestamp=datetime.now(
            timezone.utc
        ).isoformat(),

        severity=estimate_severity(
            classification
        ),

        confidence=classification.confidence,

        sources=[
            item.source
        ],

        evidences=[
            evidence
        ],

        description=classification.reason
    )