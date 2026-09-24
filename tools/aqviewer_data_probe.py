import requests
import json
from pathlib import Path


BASE = "https://discomap.eea.europa.eu/App/AQViewer"

FQN = "Airquality_Dissem.b2g.measurements"


init_url = f"{BASE}/init?fqn={FQN}"

init = requests.get(
    init_url,
    timeout=60
).json()


print("INIT OK")

request_body = init["Request"]

print(json.dumps(request_body, indent=2)[:2000])


data_url = f"{BASE}/data?fqn={FQN}"


response = requests.post(
    data_url,
    json=request_body,
    timeout=120
)


print()
print("DATA STATUS:", response.status_code)
print(response.text[:3000])


out = Path(
    "debug-results/aqviewer_data_probe"
)

out.mkdir(
    parents=True,
    exist_ok=True
)


(out/"init_request.json").write_text(
    json.dumps(request_body, indent=2),
    encoding="utf-8"
)


(out/"data_response.json").write_text(
    response.text,
    encoding="utf-8"
)