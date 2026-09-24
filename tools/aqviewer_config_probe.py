import requests
import re

url = (
    "https://discomap.eea.europa.eu/"
    "App/AQViewer/index.html?"
    "fqn=Airquality_Dissem.b2g.measurements"
)

text = requests.get(url, timeout=30).text

patterns = [
    r"https?://[^\"']+",
    r"[^\"']+\.json",
    r"[^\"']+\.js",
    r"api[^\"']*",
    r"metadata[^\"']*",
    r"measurement[^\"']*",
    r"Airquality[^\"']*",
]

for pattern in patterns:
    print("\n=== PATTERN:", pattern)
    for item in re.findall(pattern, text, flags=re.I):
        print(item)