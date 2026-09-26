EkoKontur AIR-1.6E2C3B Real Refresh Service v01

Purpose:
Add orchestration service for EEA station refresh.

Connects:
- EEA URL discovery
- parquet downloader
- station data loader

Does not:
- modify API routes
- add scheduler

Install:
python .\tools\install_air1_6e2c3b_real_refresh_service_v01.py
