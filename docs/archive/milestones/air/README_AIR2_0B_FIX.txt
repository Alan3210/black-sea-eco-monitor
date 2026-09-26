EkoKontur AIR-2.0B Evidence Timeline API Fix v01

Fix:
FastAPI Query object leaked when endpoint function called directly in tests.

Change:
pollutant parameter now uses plain default value.

Install:
python .\tools\install_air2_0b_fix_query_parameter_v01.py
