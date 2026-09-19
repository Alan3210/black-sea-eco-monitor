WEATHER-1.1 ECMWF Open Data Provider v0.1

Scope
-----
Adds a real ECMWF IFS Open Data provider behind the WEATHER-1.0 canonical
contract.

Implemented:
- source failover: google -> azure -> aws -> ecmwf;
- deterministic local GRIB cache under data/cache/weather/ecmwf;
- cache sidecar metadata with source/run/step/retrieval time;
- explicit forecast run in retrieval requests;
- native-grid bilinear point interpolation;
- u10/v10 -> canonical wind fields;
- total precipitation metres -> millimetres;
- same-run precipitation deaccumulation;
- exact provenance and quality flags;
- tests with injected fake clients/datasets, no network dependency;
- live CLI probe.

Not implemented yet:
- FastAPI weather endpoints;
- temporal interpolation between forecast steps;
- GFS fallback provider;
- OpenDrift/OpenOil wind forcing;
- frontend weather layer.

Install:
python .\tools\install_weather1_1_ecmwf_provider_v01.py

Targeted tests:
python -m pytest -q .\tests\test_ecmwf_weather_provider.py

Live probe:
python .\tools\weather1_1_ecmwf_point_probe.py --lat 44.60 --lon 37.80
Probe launch note
-----------------
The probe supports both direct execution and module execution:
python .\tools\weather1_1_ecmwf_point_probe.py --lat 44.60 --lon 37.80
python -m tools.weather1_1_ecmwf_point_probe --lat 44.60 --lon 37.80

