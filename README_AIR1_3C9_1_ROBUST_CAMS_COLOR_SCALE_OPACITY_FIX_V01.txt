AIR-1.3C.9.1 — Robust CAMS Color Scale + Opacity Fix v0.1

Fixes:
1. localStorage missing value no longer becomes Number(null)=0 -> 20%.
   Missing/empty value now uses the intended 55% default.

2. CAMS map colors use robust field percentiles:
   P5 / P25 / P50 / P75 / P95.

   This prevents isolated extreme maxima from compressing most of the
   operational field into nearly one color.

Unchanged:
- actual MIN / MEAN / MAX statistics
- popup exact concentration
- CAMS model-forecast semantics
- no safe/danger labels

After installation:
  cd D:\repository\black-sea-eco-monitor\frontend
  npm test
  npm run build
