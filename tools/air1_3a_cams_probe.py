from __future__ import annotations
import argparse, json, sys
from backend.services.cams_air_quality_provider import CamsEuropeAirQualityProvider, cams_configuration_status, default_operational_run_date

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-date", default=None)
    p.add_argument("--lead", default="0,6,12,24,48,72,96")
    p.add_argument("--pollutants", default="pm25,pm10,no2,so2,o3,dust")
    p.add_argument("--force", action="store_true")
    a = p.parse_args()
    status = cams_configuration_status()
    print(json.dumps({"ads_configuration": status}, ensure_ascii=False, indent=2))
    if not status["configured"]:
        print("ADS is not configured. Create %USERPROFILE%\\.cdsapirc first.", file=sys.stderr)
        return 2
    run_date = a.run_date or str(default_operational_run_date())
    leads = [int(x.strip()) for x in a.lead.split(",") if x.strip()]
    pollutants = [x.strip() for x in a.pollutants.split(",") if x.strip()]
    artifact = CamsEuropeAirQualityProvider().retrieve(run_date=run_date, lead_hours=leads, pollutants=pollutants, force=a.force)
    print(json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2))
    print("\nNext: AIR-1.3A.1 real NetCDF inspection.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
