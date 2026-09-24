import json
from pathlib import Path
import requests


URL = (
    "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
    "/City/GetCountryCitySpos"
)


payload = {
    "countries": ["BG", "RO"],
    "cities": [],
    "pollutants": ["PM10"],
    "dataset": 1,
    "aggregationType": "hour"
}


response = requests.post(
    URL,
    json=payload,
    timeout=120
)


print("STATUS:", response.status_code)
print(response.text[:2000])


out = Path(
    "debug-results/eea_metadata_probe"
)

out.mkdir(
    parents=True,
    exist_ok=True
)


(out / "response.json").write_text(
    response.text,
    encoding="utf-8"
)