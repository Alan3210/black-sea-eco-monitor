EkoKontur AIR-1.6E2C2 EEA Parquet Downloader v01

Purpose:
Add parquet download layer for EEA station pipeline.

Scope:
- downloads parquet files from discovered EEA URLs;
- stores files in EEA cache;
- supports cache hit.

Does not:
- parse parquet;
- fuse observations;
- modify API/frontend.

Install:
python .\tools\install_air1_6e2c2_eea_parquet_downloader_v01.py
