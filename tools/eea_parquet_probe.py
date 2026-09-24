
from pathlib import Path
import requests


API = "https://eeadmz1-downloads-api-appservice.azurewebsites.net/ParquetFile/urls"


payload = {
    "countries": ["BG", "RO"],
    "cities": [],
    "pollutants": ["PM10"],
    "dataset": 1,
    "aggregationType": "hour",
}


response = requests.post(
    API,
    json=payload,
    timeout=120,
)


print("STATUS:", response.status_code)
print(response.text[:1000])


out = Path("debug-results/eea_parquet_probe")
out.mkdir(parents=True, exist_ok=True)

(out / "urls.txt").write_text(
    response.text,
    encoding="utf-8"
)