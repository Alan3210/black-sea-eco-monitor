EkoKontur AIR-1.6D4B1 EEA Station Fusion Contract v01

Purpose:
Create isolated fusion contract between:
- EEA AQViewer station metadata
- EEA parquet measurement records

This stage:
- creates StationObservation objects;
- normalizes sampling point identifiers;
- does not connect live EEA sources;
- does not modify API/frontend.

Install:
python .\tools\install_air1_6d4b1_eea_station_fusion_contract_v01.py
