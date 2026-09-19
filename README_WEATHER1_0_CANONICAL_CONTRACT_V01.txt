WEATHER-1.0 Canonical Weather Contract v0.1

Adds:
- canonical weather Pydantic schema;
- wind u/v <-> speed/direction math;
- precipitation unit/deaccumulation semantics;
- provider-neutral WeatherProvider protocol;
- unit tests.

Does not modify:
- FastAPI routes;
- OpenDrift/OpenOil;
- frontend/Web GIS;
- existing production code paths.

Install:
python .\tools\install_weather1_0_contract_v01.py

Test:
python -m pytest -q .\tests\test_weather_math.py .\tests\test_weather_schema.py
