AIR-1.3C.9.2 — Native CAMS Grid Resolution v0.1
================================================

Purpose
-------
Render the CAMS field at the provider's native grid resolution instead
of the current stride=2 downsampled grid.

Change
------
Frontend CAMS request:
  stride=2
becomes:
  stride=1

Expected effect
---------------
Current:
  ~45 x 88 cells

Native:
  ~90 x 175 cells

So each visible cell is approximately half the current width and height.

Semantics
---------
This does NOT invent additional spatial information.
It simply stops dropping every second CAMS grid point.

No interpolation, smoothing or artificial upscaling is introduced.

After installation
------------------
cd D:\repository\black-sea-eco-monitor\frontend
npm test
npm run build

Then restart Vite or hard-refresh and compare map performance.
