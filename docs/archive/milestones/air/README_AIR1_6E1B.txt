EkoKontur AIR-1.6E1B EEA Runtime Provider v01

Purpose:
Add orchestration layer between:
- EEA metadata provider
- EEA measurement parser
- EEA station evidence fusion

This stage:
- works with existing cached/input data;
- creates StationObservation objects;
- does not download live EEA files;
- does not modify API/frontend.

Install:
python .\tools\install_air1_6e1b_eea_runtime_provider_v01.py
