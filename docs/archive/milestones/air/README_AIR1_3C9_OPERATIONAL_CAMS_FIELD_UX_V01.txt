AIR-1.3C.9 — Operational CAMS Field UX v0.1

Replaces the density-style heatmap with a concentration-driven CAMS grid.

Adds:
- actual concentration colors
- MIN / MEAN / MAX
- numeric color legend
- field opacity control
- local concentration popup on click
- model valid time and lead
- model-forecast disclaimer

No safe/danger labels are introduced.

After install:
  cd D:\repository\black-sea-eco-monitor\frontend
  npm test
  npm run build
