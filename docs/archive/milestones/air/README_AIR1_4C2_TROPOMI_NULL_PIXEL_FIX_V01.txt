AIR-1.4C.2 — TROPOMI Null Pixel Fix v0.1
=========================================

Observed failure
----------------
The new TROPOMI test expected 3 GeoJSON cells from:

  [[1e-5, null],
   [-2e-6, 3e-5]]

but runtime produced 4.

Root cause
----------
JavaScript:

  Number(null) === 0

The previous finiteNumber() implementation treated JSON null as a valid
numeric zero. This was not merely a test issue: dataMask-invalid satellite
pixels could have been rendered as false zero-value map cells.

Fix
---
finiteNumber() now explicitly rejects:

  null
  undefined
  empty string

before Number() conversion.

Scientific behavior
-------------------
- invalid/null TROPOMI pixels are skipped
- a real numeric 0 remains valid
- valid negative retrieval values remain valid
- no interpolation is introduced

Expected frontend regression
----------------------------
tests 151
pass 151
fail 0
