# ADR-003: Evidence Rendering Pipeline Ownership

## Status

Accepted

## Context

Evidence Dashboard contains multiple rendering modules.

Historical development introduced:
- legacy renderers;
- UX renderers;
- production adapters.

This created risk of modifying unused rendering paths.

## Decision

The production rendering path is:

Data
↓
Normalizer
↓
View Model
↓
Production Renderer
↓
DOM

Evidence Timeline production renderer:

`renderVerticalTimeline()`

## Rules

New UI changes must:
1. Identify the production caller.
2. Verify the view-model contract.
3. Modify production renderer only.
4. Update tests.

## Deprecated

The following modules require review before modification:
- evidenceTimelineRenderer.js
- legacy timeline render paths

## Consequences

Benefits:
- predictable ownership;
- safer changes;
- easier onboarding.

Tradeoff:
- legacy modules remain until explicitly removed.

## Alternative Rendering Path

An alternative rendering path exists:


evidenceTimelineEventBinding.js
        ↓
renderEventTimelineForPanel()
        ↓
renderEvidenceTimeline()

This path is not the primary application rendering flow.

Before modifying this path, verify whether it is still required by active features.

## Current Status

Both rendering paths exist.

The primary path is protected by architecture tests.

The alternative path requires future consolidation review.