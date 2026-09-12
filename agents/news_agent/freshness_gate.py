from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from pydantic import BaseModel

from backend.config import settings
from agents.news_agent.models import NewsItem


class FreshnessDecision(BaseModel):

    is_fresh: bool

    age_days: Optional[float] = None

    reason: str


def evaluate_news_freshness(
    item: NewsItem,
    now: Optional[datetime] = None,
) -> FreshnessDecision:

    if not item.published_at:

        return FreshnessDecision(
            is_fresh=False,
            age_days=None,
            reason=(
                "The article has no publication date, "
                "so it cannot be accepted as a live candidate."
            ),
        )

    try:

        published_at = parsedate_to_datetime(
            item.published_at
        )

    except (TypeError, ValueError, OverflowError):

        return FreshnessDecision(
            is_fresh=False,
            age_days=None,
            reason=(
                "The article publication date "
                "could not be parsed."
            ),
        )

    if published_at.tzinfo is None:

        published_at = published_at.replace(
            tzinfo=timezone.utc
        )

    published_at = published_at.astimezone(
        timezone.utc
    )

    if now is None:

        now = datetime.now(
            timezone.utc
        )

    elif now.tzinfo is None:

        now = now.replace(
            tzinfo=timezone.utc
        )

    else:

        now = now.astimezone(
            timezone.utc
        )

    age = now - published_at

    age_days = (
        age.total_seconds()
        / 86400
    )

    # A future publication date is suspicious
    # and should not pass the live gate.
    if age_days < 0:

        return FreshnessDecision(
            is_fresh=False,
            age_days=age_days,
            reason=(
                "The article publication date "
                "is in the future."
            ),
        )

    if age_days <= settings.NEWS_MAX_AGE_DAYS:

        return FreshnessDecision(
            is_fresh=True,
            age_days=age_days,
            reason=(
                f"The article is {age_days:.1f} days old "
                f"and is within the "
                f"{settings.NEWS_MAX_AGE_DAYS}-day live window."
            ),
        )

    return FreshnessDecision(
        is_fresh=False,
        age_days=age_days,
        reason=(
            f"The article is {age_days:.1f} days old "
            f"and exceeds the "
            f"{settings.NEWS_MAX_AGE_DAYS}-day live window."
        ),
    )