# Black Sea Eco Monitor Web — v0.4

Adds:
- Co-located event grouping for incidents that share one canonical map point
- Count marker instead of overlapping circles
- Group details view listing every incident at the shared point
- Drill-down from a group into an individual Event Details panel
- Back navigation from an event to its co-located incident list
- Group selection highlight
- Group behavior respects current status/category/time filters

Run:

```powershell
npm test
npm run build
```

Expected tests: 12 passed.

Then use the project-level:

```text
START_MONITOR.cmd
```

On the current data, the two Novorossiysk incidents should appear as one marker
with the number `2`. Clicking it opens the incident list; choosing either event
opens its normal evidence/details panel.
