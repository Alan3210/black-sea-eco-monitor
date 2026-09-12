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

    prompt = f"""
You are an environmental intelligence analyst
monitoring the Black Sea region.

Analyze the news item below.

TITLE:
{item.title}

SOURCE:
{item.source}

PUBLISHED:
{item.published_at}

SUMMARY:
{item.summary or "Not available"}

Classify the article using the provided JSON schema.


CLASSIFICATION


incident

A real environmental incident has occurred.


reported

A possible environmental incident has been reported
or suspected, but the underlying incident itself
has not yet been confirmed.


follow_up

The article concerns an earlier incident:

- cleanup
- extinguishing
- containment
- investigation
- recovery
- consequences
- reopening affected areas
- long-term environmental impact


background

The article is primarily about:

- research
- policy
- programmes
- projects
- scientific studies
- general environmental discussion


forecast

The article describes possible future
environmental damage that has not happened yet.


clear

Monitoring explicitly reports that pollution
or another suspected environmental incident
was not detected.


noise

The article does not describe a useful
environmental event.


GEOGRAPHY


Identify where the environmental event itself occurs.

Do not assume that the event is in the Black Sea region
just because the phrase "Black Sea" appears somewhere
in the headline or article.

location_name should describe the most specific
location supported by the supplied information.


BLACK SEA REGION


Set is_black_sea_region to true only when
the environmental event itself occurs in or
directly affects the Black Sea region.

The region includes:

- the Black Sea
- coastal waters
- relevant coastal areas
- Ukraine
- Russia
- Georgia
- Turkey
- Bulgaria
- Romania
- Crimea
- Kerch Strait
- relevant Sea of Azov incidents

Set it to false for incidents outside this region.

Use null when there is not enough information.


IS_NEW_EVENT


true:

The supplied information clearly describes
a newly occurring or recently discovered incident.


false:

The article concerns:

- an older event
- historical analysis
- cleanup
- extinguishing after the incident
- long-term consequences
- research
- policy
- background material


null:

The supplied information is insufficient
to determine this reliably.


EVENT_DATE


event_date is the date when the environmental
incident itself occurred.

It is NOT automatically the publication date.

Use YYYY-MM-DD.

Do not invent a date.

Use null when unsupported.


ENVIRONMENTAL CATEGORY


oil_spill

Use ONLY for petroleum, fuel,
hydrocarbon or petroleum-product pollution.

Examples:

- crude oil spill
- fuel oil spill
- mazut spill
- diesel spill
- petroleum contamination

The mere presence of petroleum products
does NOT automatically mean oil_spill.

Example:

A fire at a mazut terminal is industrial_fire
unless the article also states that mazut
spilled or polluted the environment.


water_pollution

Use for non-petroleum contamination of water.

Examples:

- sunflower oil spill
- vegetable oil spill
- sewage
- contaminated runoff


wildfire

Use for fires involving:

- forests
- woodland
- vegetation
- nature reserves
- wildland

Russian examples:

- лесной пожар
- природный пожар
- пожар в лесном массиве
- пожар в заповеднике


industrial_fire

Use for fire at industrial,
energy, transport or fuel infrastructure.

Examples:

- refinery fire
- oil terminal fire
- fuel depot fire
- factory fire
- industrial plant fire
- port terminal fire
- electrical substation fire

Russian examples:

- пожар на мазутном терминале
- пожар на нефтебазе
- пожар на предприятии
- пожар на заводе
- пожар на подстанции


IMPORTANT:

A normal residential house fire,
apartment fire or unrelated urban fire
is NOT automatically an environmental incident.

Do not classify an ordinary building fire
as wildfire or industrial_fire.


chemical_release

Use when chemicals or toxic substances
are released into the environment.


CONFIDENCE


Use a value from 0.0 to 1.0.

Be conservative.

If only a headline is available,
avoid confidence 1.0 unless exceptionally explicit.


OUTPUT CONSISTENCY


The structured fields are authoritative.

The reason must agree with them.

If you identify a category,
put it into category.

If you identify a location,
put it into location_name.

Use null only when information is insufficient.

Do not invent facts.


IMPORTANT DISTINCTION


"reported" does NOT mean
that a newspaper reported an incident.

Use "reported" only when
the environmental event itself is uncertain.

If the text directly states that it happened,
use "incident".


EXAMPLE 1


TITLE:

Thousands of Tons of Sunflower Oil Spill
Into Black Sea After Strike on Odesa Region Port

classification: incident
category: water_pollution
location_name: Odesa
is_black_sea_region: true
is_new_event: true
event_date: null


EXAMPLE 2


TITLE:

Новороссийск атаковали беспилотники,
сообщается о пожаре на мазутном терминале

classification: incident
category: industrial_fire
location_name: Novorossiysk
is_black_sea_region: true

A fire at a mazut terminal is an industrial fire.
Do not infer an oil spill unless a spill
or environmental contamination is explicitly reported.


EXAMPLE 3


TITLE:

Сразу три лесных пожара тушат в Новороссийске

classification: incident
category: wildfire
location_name: Novorossiysk
is_black_sea_region: true


EXAMPLE 4


TITLE:

Мужчина и женщина погибли при пожаре в доме

classification: noise

A residential house fire alone is not
an environmental monitoring event.
"""

    response = client.chat(
        model=settings.OLLAMA_MODEL,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        format=schema,

        think=False,

        options={
            "temperature": 0
        }
    )

    result = NewsClassification.model_validate_json(
        response.message.content
    )

    fallback_text = (
        f"{item.title} "
        f"{item.summary or ''}"
    )

    updates = {}

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

    if updates:

        result = result.model_copy(
            update=updates
        )

    return result