EkoKontur AIR-1.6E2B Station Data Loader v01

Purpose:
Add cache-based loader layer between ground station service and EEA runtime provider.

Scope:
- loads prepared metadata cache;
- loads prepared measurement cache;
- delegates fusion to runtime provider.

Does not:
- download live EEA data;
- modify API router;
- modify frontend.

Install:
python .\tools\install_air1_6e2b_station_data_loader_v01.py
