AIR-1.4B.1 — Latest Available Sentinel-5P Field v0.1
=====================================================

Problem confirmed with real data
--------------------------------
At 2026-09-20 during the live probe:
- exact 2026-09-20 NRTI field had 0 valid pixels
- exact 2026-09-19 NRTI field had 37,158 valid pixels
- valid coverage on 2026-09-19 was 58.98095238095238%

Therefore "current UTC day" cannot safely mean "latest available satellite
observation".

New default behavior
--------------------
GET /air/satellite-field

When date is omitted:
1. request current UTC day
2. inspect valid_pixel_count
3. if empty, walk backward day by day
4. return the first field with valid TROPOMI pixels
5. default lookback = 7 days
6. API allows lookback_days=0..14
7. if the entire horizon is empty -> HTTP 404

When date is explicit:
GET /air/satellite-field?date=2026-09-19
the API returns that exact day only, including an empty field if that day
really has no valid pixels.

Response selection metadata
---------------------------
selection.mode
selection.reference_date
selection.resolved_date
selection.lookback_days
selection.max_lookback_days
selection.candidates_checked

Scientific rules unchanged
--------------------------
- satellite_observation
- NOT surface concentration
- dataMask invalid pixels -> null
- valid negative retrievals preserved
- no interpolation
- stride skips pixels only

Targeted tests
--------------
python -m pytest -q tests/test_sentinel5p_satellite_field.py

Live probe of latest available
------------------------------
python -m tools.air1_4b_satellite_field_probe \
  --product no2 \
  --timeliness NRTI \
  --stride 4
