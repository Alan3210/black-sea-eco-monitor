# Project Milestone Archive

This directory contains historical implementation notes, engineering checkpoints, and development milestones.

These documents are preserved for project history and traceability.
They are not the primary project documentation.

For current project information see:

- `/README.md`

---

# Archive Structure

## air/

Historical AIR pipeline milestones.

Contains development notes related to:

- CAMS air quality integration;
- Sentinel-5P / TROPOMI air monitoring;
- GEOS-CF cross-check pipelines;
- ground station evidence pipelines;
- event dashboard development;
- AIR-3.4 localization and dashboard intelligence layers.

Examples:

- `README_AIR1_*` — initial air monitoring pipeline stages
- `README_AIR2_*` — operational evidence dashboard evolution
- `README_AIR3_*` — event intelligence and dashboard integration
- `README_AIR3_4G*` — localization and UX refinement stages

---

## weather/

Historical weather and forcing milestones.

Contains development notes related to:

- ECMWF provider integration;
- wind fields;
- currents + wind forcing;
- WebGIS weather visualization;
- particle visualization.

Examples:

- `README_WEATHER1_*`

---

## satellite/

Historical satellite pipeline milestones.

Contains development notes related to:

- satellite observation APIs;
- Sentinel-1 experiments;
- SAR dark spot candidates;
- satellite data storage and import workflows.

Examples:

- `README_SATELLITE_*`
- `README_SAT*`

---

## system/

Historical system architecture milestones.

Contains development notes related to:

- monitor context;
- operator dashboard;
- Web GIS architecture;
- drift impact workflows;
- impact registry.

Examples:

- `README_SYSTEM*`

---

# Notes

Milestone files describe development history and intermediate implementation states.

When investigating current behavior:

1. Start with `/README.md`.
2. Review current source code.
3. Use milestone documents only as historical context.

## Development history

Historical milestone notes are archived in:

`docs/archive/milestones/`

The archive contains previous AIR, WEATHER, SATELLITE and SYSTEM implementation checkpoints.