WEATHER-1.3A ECMWF Wind Forcing Cube v0.1

Purpose
-------
Prepare operational ECMWF wind for OpenDrift as a native time-dependent
forcing reader, without changing the existing drift model yet.

Pipeline
--------
ECMWF IFS Open Data forecast steps
  -> WEATHER-1.1 mirror failover + GRIB cache
  -> local Black Sea / scenario bbox crop
  -> normalize scalar GRIB valid_time into a true 1-D time dimension
  -> concatenate native forecast slices
  -> xarray Dataset(time, latitude, longitude)
  -> OpenDrift generic reader
       u10 -> x_wind
       v10 -> y_wind

Important semantics
-------------------
- Native ECMWF forecast steps are preserved.
- The cube includes a step at/before simulation start and a step at/after
  simulation end so the OpenDrift reader can interpolate in time.
- No synthetic high-resolution atmospheric grid is created.
- No manual "current + N% wind" vector arithmetic is performed here.
- No changes are made to OceanDrift yet.
- No waves/Stokes drift or oil weathering are added.

Live probe
----------
python .\tools\weather1_3a_wind_forcing_probe.py --lat 44.60 --lon 37.80 --hours 12

Install
-------
python .\tools\install_weather1_3a_wind_forcing_cube_v01.py

Targeted tests
--------------
python -m pytest -q .\tests\test_ecmwf_wind_forcing.py
