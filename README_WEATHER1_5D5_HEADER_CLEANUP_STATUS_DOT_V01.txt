WEATHER-1.5D.5 — Header Cleanup + Status Dot v0.1
====================================================

Requested UI cleanup
--------------------
1. Add a small visible gap between the fixed top bar and the left sidebar.
2. Remove the visible eyebrow:
     ЭКОЛОГИЧЕСКАЯ АНАЛИТИКА
3. Rename:
     Экомонитор Чёрного моря
   to:
     ЭКОМОНИТОР
4. Remove visible right-side text:
     Мониторинг активен
     Обновлено <time>
5. Keep the live green/yellow/red connection indicator and place it at
   the far-right edge of the top bar.

Implementation
--------------
- Main title is now ECOMONITOR / ЭКОМОНИТОР.
- The eyebrow is removed from the DOM.
- Connection/update labels remain in the DOM as visually hidden live
  status text so existing JS and accessibility behavior are preserved.
- Only the status dot is visible.
- Status dot is the rightmost item after the language switch.
- Desktop filter panel top offset:
    138 px -> 152 px
- Desktop event panel top offset:
    138 px -> 152 px

This creates a clear visual air gap below the header.

Scientific scope
----------------
UI layout/text only.

No changes to:
- wind speed;
- current speed;
- ECMWF;
- Copernicus;
- combined field timing;
- OpenDrift;
- impact analysis;
- backend APIs.

Install
-------
Extract into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5d5_header_cleanup_status_dot_v01.py

Regression
----------
No JavaScript logic changed.

Expected frontend regression:
  tests 116
  pass 116
  fail 0

Then:
  npm run build

Live validation
---------------
1. Ctrl+F5.
2. Confirm title is:
     ЭКОМОНИТОР
3. Confirm there is no visible:
     ЭКОЛОГИЧЕСКАЯ АНАЛИТИКА
     Мониторинг активен
     Обновлено ...
4. Confirm the live status dot remains at the far-right edge.
5. Confirm there is a visible gap between the top bar and left sidebar.
6. Confirm combined wind/current operational status still works.
