# Black Sea Eco Monitor Web v0.9.1 — Long-running Task UX

Small UX release on top of v0.9 Drift Map Step 2.

## What changed

Long Copernicus and OpenDrift requests now show a clear non-blocking waiting state:

- animated spinner;
- indeterminate progress bar;
- live elapsed timer;
- realistic expectation message;
- a longer-wait message when a request exceeds its normal range;
- the map remains interactive while the request is running.

### Surface currents

After ~0.65 s a waiting card appears. It explains that Copernicus can take 30–120 seconds. After 2 minutes the wording changes to indicate that the request is slow but still active.

### OpenDrift

After ~0.45 s a waiting card appears. It explains that the calculation usually takes 1–3 minutes. After 3 minutes the wording changes and explicitly tells the user not to submit a duplicate calculation.

While OpenDrift is running, its point/horizon/particle controls are locked so the pending response cannot become inconsistent with changed settings. The map itself remains usable.

The currents loader also rejects duplicate refresh calls while a currents request is already in progress.

## Install

Extract over:

```text
D:\repository\black-sea-eco-monitor\frontend
```

No backend changes.

## Test

```powershell
cd D:\repository\black-sea-eco-monitor\frontend
npm test *> frontend_v091_test.txt
Get-Content frontend_v091_test.txt -Tail 20
```

Expected: `57 passed`.

## Build

```powershell
npm run build *> frontend_v091_build.txt
Get-Content frontend_v091_build.txt -Tail 20
```

Then restart with the normal project launcher.

## Visual QA

1. Enable Surface Currents after a cold start.
2. Confirm the waiting card appears if the request is not immediate.
3. Confirm elapsed time increments every second.
4. Run a 6 h / 100-particle drift forecast.
5. Confirm the OpenDrift waiting card appears and the map can still be panned/zoomed.
6. Confirm drift configuration controls are temporarily disabled while the request is running.
7. Confirm the waiting card disappears when results arrive or an error is returned.
8. Switch RU/EN during normal use and confirm labels remain localized.
