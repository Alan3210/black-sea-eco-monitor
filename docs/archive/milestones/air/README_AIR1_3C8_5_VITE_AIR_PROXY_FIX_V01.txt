AIR-1.3C.8.5 — Vite Air Proxy Fix v0.1
======================================

Problem
-------
The CAMS frontend requests:
  /air/field

The Vite dev server currently proxies /weather and other backend routes,
but not /air. Therefore Vite can return index.html for /air/field, and
response.json() fails with:
  JSON.parse: unexpected character at line 1 column 1

Fix
---
Add:
  '/air': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: false,
  },

to frontend/vite.config.js.

After install
-------------
Restart Vite:
  cd D:\repository\black-sea-eco-monitor\frontend
  npm run dev -- --force

Then hard-refresh the browser and enable:
  Air quality · CAMS
