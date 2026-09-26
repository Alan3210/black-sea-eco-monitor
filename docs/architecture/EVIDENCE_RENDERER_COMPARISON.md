# Evidence Renderer Comparison

## Purpose

This document describes the current Evidence Timeline rendering paths.

The goal is to document ownership and differences before future consolidation.

No renderer removal is proposed.

---

# Current Rendering Paths

## Primary Production Path

Status:

Active

Flow:


Evidence payload
        |
        v
buildProductionTimelineBlock()
        |
        v
renderVerticalTimeline()
        |
        v
DOM

Main renderer:


evidenceTimelineUX.js

Function:


renderVerticalTimeline()

Responsibilities:

- build timeline cards;
- apply visual states;
- generate timeline markup.

---

## Alternative Rendering Path

Status:

Review

Flow:


Event binding
        |
        v
renderEventTimelineForPanel()
        |
        v
renderEvidenceTimeline()
        |
        v
DOM

Files:


evidenceTimelineEventBinding.js
evidenceTimelineRenderer.js

Current state:

- path exists;
- tests exist;
- not confirmed as primary application path.

---

# Renderer Comparison

| Area | renderVerticalTimeline | renderEvidenceTimeline |
|---|---|---|
| File | evidenceTimelineUX.js | evidenceTimelineRenderer.js |
| Status | Production | Alternative |
| Visual model | TIMELINE_VISUAL_STATES | buildVisualTimeline() |
| i18n | Yes | Yes |
| Time | Yes | Yes |
| Source | Yes | Yes |

---

# Architectural Difference

## Production renderer

Pipeline:


event
 |
 v
buildTimelineCard()
 |
 v
buildVerticalTimeline()
 |
 v
renderVerticalTimeline()

Responsibilities are separated:


Data
 ↓
View Model
 ↓
Renderer
 ↓
DOM

---

## Alternative renderer

Pipeline:


event
 |
 v
buildVisualTimeline()
 |
 v
HTML generation

This renderer owns more presentation decisions.

---

# Current Decision

Both paths remain in the repository.

Primary rendering path:


renderVerticalTimeline()

Alternative path:


renderEvidenceTimeline()

Before modifying the alternative path, verify active usage.

---

# Future Consolidation

Possible migration:


renderEventTimelineForPanel()
    ↓

production timeline pipeline
    ↓

renderVerticalTimeline()

Before removing any module:

1. verify usage;
2. migrate callers;
3. update tests;
4. remove only after validation.

---

# Related Documents

- ADR-003: Evidence Rendering Pipeline Ownership