# Black Sea Eco Monitor Web — v0.5

Adds Data Quality visibility to the operator UI.

## New in v0.5

- Reads `location.type`, `location.confidence`, and `location.source` from the canonical Monitor API.
- Reads `time.incident_time`, `time.detection_time`, and `time.source_time`.
- Event Details now separates event confidence from location confidence.
- Adds a Location Quality section with location type, map scope, and coordinate source.
- Canonical database coordinates are explicitly labeled as representative map points, not exact incident coordinates.
- Timeline shows incident time, source publication time, detection time, first seen, and latest time.
- Time-window filtering now prefers:
  1. incident time
  2. source time
  3. detection time
  4. legacy last-seen / updated / first-seen timestamps
- Co-located incident grouping remains unchanged.

Run:

```powershell
npm test
npm run build
```

Expected tests: 17 passed.

Then use the project-level launcher:

```text
START_MONITOR.cmd
```

Open any incident in the right-side Event Details panel and verify the new
`LOCATION QUALITY` and expanded `TIMELINE` sections.
