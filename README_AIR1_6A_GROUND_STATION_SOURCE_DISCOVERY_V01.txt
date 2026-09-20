AIR-1.6A — Ground Station Source Discovery v0.1
================================================

Decision
--------
Use the official European Environment Agency Air Quality Download Service
as the FIRST production ground-station provider.

EEA role:
  primary_station_measurement_source

EEA Black Sea scope:
  Bulgaria (BG)
  Romania (RO)

EEA dataset:
  E2a / Up-To-Date / unverified
  dataset id = 1

EEA pollutants:
  PM2.5
  PM10
  NO2
  O3
  SO2
  CO

EEA aggregation:
  hourly

Important semantics
-------------------
E2a is real station measurement data, but up-to-date E2a is UNVERIFIED.
Do not label it verified/validated station truth.

Why EEA is not enough for the whole Black Sea
----------------------------------------------
The current official EEA /Country endpoint includes BG and RO, but does
not include TR, GE, UA or RU.

Therefore local-source tracks remain necessary.

Türkiye
-------
Official source:
  Ulusal Hava Kalitesi Izleme Agi
  https://www.havaizleme.gov.tr/

Official government material states hourly raw station data are published
online and the national network contains hundreds of stations.

Decision:
  strong official source candidate
  stable documented public machine API still needs validation

Georgia
-------
Official source:
  National Environmental Agency
  https://air.gov.ge/en/

The official portal provides continuous automatic-station measurements.
Batumi is explicitly part of the network.

Decision:
  strong official Black Sea source candidate
  stable documented public machine API still needs validation

Ukraine
-------
Official sources include Data.gov.ua and EcoZagroza.
Daily/monthly official hydrometeorological datasets are available.

Decision:
  secondary/local provider track
  near-real-time coastal machine feed still requires validation

Russia
------
Official monitoring exists, including monitoring in Krasnodar Krai.

Decision:
  local source track
  no stable documented public near-real-time machine API validated in
  AIR-1.6A discovery

OpenAQ
------
Remains excluded from the architecture.

Live validation
---------------
After installation:

python -m tools.air1_6a_ground_station_source_probe

The probe:
- calls official EEA /Country
- confirms live BG/RO scope
- confirms TR/GE/UA/RU absence from current EEA country endpoint
- calls EEA /DownloadSummary for BG and RO E2a hourly data
- checks reachability of selected official local portals
- writes:
  validation/air1_6a_ground_station_sources.json

Caveat
------
EEA DownloadSummary is a source-availability/file summary check.
Per official EEA documentation, summary requests do not apply datetime or
aggregation filters. AIR-1.6B must validate actual recent measurement
timestamps by downloading and inspecting selected E2a parquet data.
