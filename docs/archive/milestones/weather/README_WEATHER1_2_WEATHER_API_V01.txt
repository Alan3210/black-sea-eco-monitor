WEATHER-1.2 Weather API v0.1

Scope
-----
Expose the WEATHER-1 canonical point-weather contract through FastAPI.

Endpoint
--------
GET /weather/point

Required query parameters:
- latitude  [-90, 90]
- longitude [-180, 180]

Optional:
- valid_time ISO-8601 datetime

Response:
Canonical WeatherPoint from WEATHER-1.0, including:
- u10/v10;
- derived wind speed and meteorological FROM direction;
- precipitation rate/accumulation;
- exact forecast/run provenance;
- source/fallback/quality flags.

HTTP semantics:
- 200: canonical weather point returned;
- 422: invalid coordinates or requested time outside provider horizon;
- 503: operational provider/source unavailable.

Architecture
------------
The API depends on WeatherProvider through FastAPI dependency injection.
The default provider is ECMWF IFS Open Data from WEATHER-1.1. Tests override
the dependency and never make network calls.

Still NOT included:
- OpenDrift/OpenOil wind forcing;
- Web GIS weather visualization;
- GFS fallback provider;
- temporal interpolation.

Install from repository root:
python .\tools\install_weather1_2_weather_api_v01.py

Targeted tests:
python -m pytest -q .\tests\test_weather_api.py
