WEATHER-1.1 direct probe launch fix v0.1

Purpose:
Fix ModuleNotFoundError when running:
python .\tools\weather1_1_ecmwf_point_probe.py

The patch also updates the WEATHER-1.1 installer so reinstalling it does not
restore the broken probe source.

Install from repository root:
python .\tools\install_weather1_1_probe_run_fix_v01.py
