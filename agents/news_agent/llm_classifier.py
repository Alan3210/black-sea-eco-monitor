import logging
import re
import time

import httpx
from ollama import Client

from backend.config import settings

from agents.news_agent.models import NewsItem
from agents.news_agent.classification import (
    NewsClassification,
)
from agents.news_agent.rule_classifier import (
    detect_category,
    detect_location,
)


logger = logging.getLogger(__name__)


LLM_MAX_ATTEMPTS = 3
LLM_RETRY_DELAY_SECONDS = 1.0
MAX_REASON_LENGTH = 240


def _build_prompt(
    item: NewsItem
) -> str:

    return f"""
You are an environmental intelligence analyst monitoring the Black Sea region.

Analyze only the information explicitly present in the supplied news item.
Do not infer facts from the reputation of a city, military context, proximity
 to the sea, or what might usually happen in similar incidents.

TITLE:
{item.title}

SOURCE:
{item.source}

PUBLISHED:
{item.published_at}

SUMMARY:
{item.summary or "Not available"}

Return a result that matches the provided JSON schema.

CLASSIFICATION

incident
- A real environmental incident is explicitly described as happening now or
  having just occurred.
- Active firefighting such as "тушат" or "ликвидируют пожар" can still be an
  incident when the event is ongoing.

reported
- The possible environmental incident itself is uncertain, suspected, or
  unconfirmed.
- Do not use reported merely because a newspaper reported the story.

follow_up
- The article is mainly about an already known incident after the main event.
- Examples: cleanup, completed extinguishing, containment, recovery,
  investigation, consequences, reopening, long-term impact.
- Russian completed wording such as "потушили", "ликвидирован" or
  "локализован" normally indicates follow_up.

background
- Research, policy, programmes, projects, historical context, scientific or
  general environmental discussion.

forecast
- Possible future environmental damage that has not happened yet.

clear
- Monitoring explicitly says pollution or another suspected incident was not
  detected.

noise
- The article does not establish a useful environmental event in one of the
  supported environmental categories below.
- A generic urban fire, residential fire, casualty event, or military attack
  is noise unless the supplied text explicitly establishes an environmental
  category.

ENVIRONMENTAL CATEGORIES

oil_spill
- Petroleum, fuel, hydrocarbon, mazut, diesel or petroleum-product pollution.
- Requires an explicit spill, leak, discharge, contamination or pollution
  signal.
- A fire at a fuel facility is not automatically an oil spill.

water_pollution
- Non-petroleum contamination of water, such as sewage, sunflower/vegetable
  oil spill, contaminated runoff or other explicitly described water pollution.

wildfire
- Fire involving forest, woodland, vegetation, wildland, nature reserve or
  similar natural terrain.

industrial_fire
- Fire at explicitly identified industrial, energy, transport or fuel
  infrastructure.
- Examples: refinery, oil terminal, fuel depot, factory, industrial plant,
  port terminal, electrical substation.
- NEVER infer industrial_fire merely because the location is a port city,
  coastal city, military target, or near the sea.
- If the text only says that a fire happened on a street, embankment, building,
  or unspecified urban location, do not assign industrial_fire.

chemical_release
- Chemicals or toxic substances are explicitly released into the environment.

algae_bloom
- An algae/algal bloom is explicitly described.

marine_animal_death
- Explicit mortality or mass death of marine animals or fish.

storm_damage
- Explicit storm, flood, coastal storm, or severe-weather damage relevant to
  environmental monitoring.

CATEGORY DISCIPLINE

- Do not invent a category.
- If no supported environmental category is established by the text, use
  category=null.
- If a fire is real but the text does not establish wildfire or industrial
  infrastructure, classify it as noise rather than inventing a category.

GEOGRAPHY

- location_name must be the most specific location supported by the text.
- Do not invent a district, street, facility or coordinates.

BLACK SEA REGION

Set is_black_sea_region=true only when the event itself occurs in or directly
 affects the Black Sea, Sea of Azov, or a relevant Black Sea coastal area.
Examples include coastal Krasnodar Krai, Crimea, Sevastopol, Odesa region,
Georgia's Black Sea coast, Turkey's Black Sea coast, Bulgaria and Romania.

Do not mark an event as Black Sea merely because it is somewhere in Russia,
Ukraine, Georgia or Turkey. Use false outside the region and null when the
location is insufficient.

IS_NEW_EVENT

true
- Clearly a newly occurring or recently discovered incident.

false
- Older event, completed response, cleanup, recovery, long-term consequences,
  research, policy or background material.

null
- Insufficient information.

EVENT_DATE

- Date when the environmental incident itself occurred, YYYY-MM-DD.
- Publication date is not automatically the event date.
- Never invent a date. Use null when unsupported.

CONFIDENCE

- Use 0.0 to 1.0.
- Be conservative, especially when only a headline is available.

OUTPUT RULES

- Structured fields are authoritative and must agree with each other.
- Do not output internal reasoning, alternatives, self-correction, debate,
  speculation, or chain-of-thought.
- reason MUST be exactly one short factual sentence, maximum 25 words.
- Do not repeat the prompt or discuss alternative classifications.

EXAMPLES

1) "Новороссийск атаковали беспилотники, сообщается о пожаре на мазутном терминале"
classification: incident
category: industrial_fire
location_name: Novorossiysk
is_black_sea_region: true

2) "Сразу три лесных пожара тушат в Новороссийске"
classification: incident
category: wildfire
location_name: Novorossiysk
is_black_sea_region: true

3) "Мужчина и женщина погибли при пожаре в доме"
classification: noise
category: null

4) "Севастопольские огнеборцы ликвидируют пожар в районе улицы Горпищенко"
classification: noise
category: null
location_name: Sevastopol
is_black_sea_region: true

5) "Пожар в лесном массиве заповедника на Большом Утрише локализован"
classification: follow_up
category: wildfire
is_new_event: false
"""


def _chat_with_retry(
    client: Client,
    schema: dict,
    prompt: str,
):

    last_error = None

    for attempt in range(
        1,
        LLM_MAX_ATTEMPTS + 1,
    ):

        try:

            return client.chat(
                model=settings.OLLAMA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                format=schema,
                think=False,
                options={
                    "temperature": 0,
                },
            )

        except httpx.TransportError as error:

            last_error = error

            if attempt >= LLM_MAX_ATTEMPTS:
                raise

            delay = (
                LLM_RETRY_DELAY_SECONDS
                * attempt
            )

            logger.warning(
                "Temporary Ollama transport error "
                "on attempt %s/%s: %s. "
                "Retrying in %.1f seconds.",
                attempt,
                LLM_MAX_ATTEMPTS,
                error,
                delay,
            )

            time.sleep(
                delay
            )

    if last_error is not None:
        raise last_error

    raise RuntimeError(
        "Ollama request failed without an error."
    )


def _compact_reason(
    reason: str
) -> str:

    clean_reason = " ".join(
        reason.split()
    )

    sentences = re.split(
        r"(?<=[.!?])\s+",
        clean_reason,
        maxsplit=1,
    )

    compact = sentences[0].strip()

    if len(compact) <= MAX_REASON_LENGTH:
        return compact

    return (
        compact[:MAX_REASON_LENGTH - 3]
        .rstrip()
        + "..."
    )


def classify_news_with_llm(
    item: NewsItem
) -> NewsClassification:

    client = Client(
        host=settings.OLLAMA_BASE_URL
    )

    schema = (
        NewsClassification
        .model_json_schema()
    )

    prompt = _build_prompt(
        item
    )

    response = _chat_with_retry(
        client=client,
        schema=schema,
        prompt=prompt,
    )

    result = (
        NewsClassification
        .model_validate_json(
            response.message.content
        )
    )

    fallback_text = (
        f"{item.title} "
        f"{item.summary or ''}"
    ).lower()

    updates = {
        "reason": _compact_reason(
            result.reason
        )
    }

    if result.category is None:

        fallback_category = detect_category(
            fallback_text
        )

        if fallback_category is not None:

            updates["category"] = (
                fallback_category
            )

    if result.location_name is None:

        fallback_location = detect_location(
            fallback_text
        )

        if fallback_location is not None:

            updates["location_name"] = (
                fallback_location
            )

    return result.model_copy(
        update=updates
    )
