EkoKontur AIR-1.6D1 EEA Station Provider v01

Purpose:
Add the first isolated EEA ground station provider layer.

This stage does NOT:
- modify API routes;
- modify frontend;
- load real station data into Web GIS.

This stage adds:
- backend/services/eea_station_provider.py
- tests/test_eea_station_provider.py

Installer:
python .\tools\install_air1_6d1_eea_station_provider_v01.py

Installer actions:
- verify prerequisites;
- create dev-snapshots backup;
- copy payload;
- remove temporary payload folder;
- run verification test.
