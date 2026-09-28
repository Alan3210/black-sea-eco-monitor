# ADR-004: Evidence Fusion and Investigation Layer

## Status

Accepted

## Date

2026-09-28

## Context

Black Sea Eco Monitor combines multiple environmental data sources and analytical components:

- satellite observations;
- atmospheric models;
- meteorological data;
- ocean and drift modelling;
- ground station measurements;
- impact forecasting.

The next stage of the project must move beyond answering:

> What environmental event occurred?

and begin supporting:

> What evidence supports this event, what environmental conditions contributed to it, and what possible sources may explain it?

Future integrations such as AIS vessel tracking, OpenOil backtracking, satellite pass prediction, thermal anomalies and natural-hazard feeds must not become isolated UI layers.

They must integrate through a common investigation model.

## Problem

Without a shared evidence contract, every provider risks introducing its own:

- data schema;
- confidence representation;
- rendering logic;
- event linkage;
- provenance format;
- investigation UI.

This would create parallel pipelines and make investigation and source attribution difficult.

## Decision

Introduce an Evidence Fusion Layer.

Canonical flow:

```text
External / Internal Data Sources
        |
        v
Provider Adapters
        |
        v
Evidence Normalizers
        |
        v
Canonical Evidence Records
        |
        v
Evidence Aggregation
        |
        v
Event Investigation View Model
        |
        v
Renderers
        |
        v
Evidence Dashboard / Map

This extends the existing project pipeline:
normalizer
    ↓
view-model
    ↓
renderer
    ↓
DOM

Raw provider data must not be rendered directly.
Canonical Evidence Record
All investigation-capable sources should map into a common evidence contract.
Conceptual structure:
{
  "id": "evidence_001",
  "eventId": "event_123",
  "type": "satellite_observation",
  "source": "Sentinel-1",
  "timestamp": "2026-09-28T12:00:00Z",
  "location": {
    "lat": 44.72,
    "lon": 37.45
  },
  "confidence": 0.86,
  "metadata": {},
  "provenance": {}
}

The physical storage schema may evolve, but the semantic contract should remain stable.
Evidence Types
Initial types:
SATELLITE_OBSERVATION
ATMOSPHERIC_MODEL
WEATHER_CONDITION
OCEAN_DRIFT
GROUND_MEASUREMENT
IMPACT_FORECAST

Future types:
VESSEL_POSITION
VESSEL_TRACK
POSSIBLE_VESSEL_SOURCE
INDUSTRIAL_SOURCE
THERMAL_ANOMALY
NATURAL_HAZARD
SATELLITE_PASS
BACKTRACK_ORIGIN

New providers should preferably map to an existing evidence type before introducing another one.
Provenance
Every evidence record must retain enough information to identify its origin.
Where available:
- provider;
- dataset;
- source identifier;
- observation time;
- ingestion time;
- processing method;
- model or algorithm version.
Evidence without provenance must not be treated as equivalent to fully traceable evidence.
Confidence Semantics
confidence represents confidence in an evidence record or analytical result.
It must not automatically mean:
- probability that a particular actor caused an incident;
- legal responsibility;
- certainty of pollution attribution.
For example:
Satellite observation confidence: 0.90

does not mean:
90% probability that vessel X caused the spill.

Source attribution requires a separate analytical model.
Evidence Aggregation
Evidence records linked to one event may be aggregated into an investigation model.
Example:
Environmental Event
        |
        +-- Satellite observation
        +-- Weather conditions
        +-- Ocean drift
        +-- Ground measurements
        +-- Impact forecast
        +-- Vessel evidence

Individual evidence records must remain accessible and must not be collapsed into one opaque score.
Investigation View Model
The frontend must consume investigation data through a view-model.
Conceptual structure:
InvestigationViewModel
    event
    evidence[]
    timeline[]
    environmentalContext
    candidateSources[]
    impact

The model should remain extensible.
Backend Responsibilities
The backend owns:
- provider adapters;
- evidence normalization;
- evidence persistence;
- event-to-evidence relationships;
- evidence aggregation;
- analytical evidence generation;
- future source-attribution logic.
Frontend Responsibilities
The frontend may:
- group evidence by type;
- display provenance;
- display confidence;
- display evidence on the map;
- connect evidence to the timeline;
- display candidate sources.
The frontend must not infer causal responsibility directly from raw provider data.
API Direction
A future event-oriented API should expose normalized investigation evidence.
Example:
GET /events/{event_id}/evidence

Conceptual response:
{
  "eventId": "event_123",
  "evidence": [],
  "candidateSources": []
}

The final route and schema must be aligned with the existing backend before implementation.
AIS Integration
AIS should be integrated as an evidence provider, not only as a map layer.
Expected future flow:
AIS Provider
    |
    v
Vessel Ingestion Agent
    |
    v
Vessel Position / Track Store
    |
    v
AIS Evidence Normalizer
    |
    v
Evidence Fusion Layer

Map visualisation of vessels is optional and independent from storing vessel evidence for investigations.
OpenOil Backtracking
OpenOil backtracking may produce analytical evidence such as:
BACKTRACK_ORIGIN

This result can later be compared with:
- historical vessel tracks;
- ports;
- coastal infrastructure;
- industrial sources;
- other known sources.
Backtracking evidence must retain model parameters and provenance.
Source Attribution
Source attribution is a separate analytical layer.
Conceptual flow:
Pollution Detection
        |
        v
Environmental Evidence
        |
        v
Backtracking
        |
        v
Candidate Source Search
        |
        v
Evidence Matching
        |
        v
Candidate Sources

Candidate sources must be presented as hypotheses supported by evidence.
The system must preserve the distinction between:
- observation;
- correlation;
- model output;
- attribution hypothesis.
Investigation UI
The Evidence Dashboard should evolve from:
Sources
Timeline
Impact

towards:
Investigation

Evidence
Timeline
Environmental Context
Possible Sources
Impact

The existing Evidence Dashboard lifecycle should be reused rather than replaced.
Non-Goals
This ADR does not:
- implement AIS ingestion;
- implement OpenOil backtracking;
- identify a polluter;
- introduce a global confidence score;
- replace the Event Store;
- replace MapLibre;
- redesign the complete Evidence Dashboard.
Those changes require separate implementation stages.
Testing Requirements
Every evidence provider must include tests for:
1. normalization;
2. provenance;
3. event linkage;
4. malformed or incomplete provider data;
5. stable frontend view-model contracts.
Frontend tests should verify contracts rather than hardcoded presentation text.
Architecture Rules
1. Raw provider data must not be rendered directly.
2. Provider-specific structures must be normalized.
3. Evidence must retain provenance.
4. Investigation UI consumes view-models, not raw API responses.
5. Observation confidence and source-attribution confidence are separate concepts.
6. New evidence providers integrate through the common evidence contract.
7. Existing production render paths must be identified before modification.
Consequences
Positive
- consistent provider integration;
- traceable evidence chains;
- safer AIS and OpenOil integration;
- better explainability;
- reduced provider-specific frontend code;
- foundation for source attribution.
Trade-offs
- additional abstraction layer;
- existing sources will require normalization;
- contracts must remain backward compatible;
- confidence semantics require discipline;
- attribution requires additional analytical services.
Planned Implementation Sequence
Phase 1
Canonical Evidence Record and aggregation foundation.
Phase 2
Integrate existing sources:
- satellite;
- weather;
- ocean drift;
- ground measurements;
- impact forecast.
Phase 3
AIS vessel intelligence.
Phase 4
OpenOil backtracking and candidate-source matching.
Phase 5
Additional contextual evidence:
- satellite pass prediction;
- thermal anomalies;
- natural hazards;
- industrial sources.
Related Documents
- docs/architecture/TECHNICAL_PASSPORT.md
- docs/decisions/ADR-003-evidence-rendering-pipeline.md
- docs/architecture/EVIDENCE_RENDERER_COMPARISON.md
