EkoKontur AIR-1.6E1A Ground Station Service Adapter v01

Purpose:
Introduce provider-aware ground station service adapter.

Scope:
- keeps existing API routes unchanged;
- adds source selection abstraction;
- prepares service layer for EEA provider connection.

Does not:
- change frontend;
- change API router;
- download live station data.

Install:
python .\tools\install_air1_6e1a_ground_station_service_adapter_v01.py
