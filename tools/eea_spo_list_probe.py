import json
from pathlib import Path
import requests


URL = (
    "https://eeadmz1-downloads-api-appservice.azurewebsites.net"
    "/List"
)


payload = {
    "countries": ["BG"],
    "cities": [],
    "pollutants": ["PM10"],
    "dataset": 1,
    "aggregationType": "hour"
}


r = requests.post(
    URL,
    json=payload,
    timeout=120
)


print("STATUS:", r.status_code)
print(r.text[:3000])


out = Path(
    "debug-results/eea_spo_list_probe"
)

out.mkdir(
    parents=True,
    exist_ok=True
)


(out / "response.json").write_text(
    r.text,
    encoding="utf-8"
)