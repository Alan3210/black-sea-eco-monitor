import requests
import re

url = "https://discomap.eea.europa.eu/App/AQViewer/index.html?fqn=Airquality_Dissem.b2g.measurements"

text = requests.get(url, timeout=30).text

scripts = re.findall(
    r'<script[^>]+src="([^"]+)',
    text
)

for item in scripts:
    print(item)