from pathlib import Path
import pandas as pd
import requests


URL = "https://eeadmz1batchservice02.blob.core.windows.net/airquality-p/BG/SPO-BG0071A_00005_100.parquet"


out = Path("debug-results/eea_parquet_probe")
out.mkdir(parents=True, exist_ok=True)


file_path = out / "sample.parquet"


response = requests.get(URL, timeout=120)
response.raise_for_status()

file_path.write_bytes(response.content)


df = pd.read_parquet(file_path)


print("ROWS:", len(df))
print()
print("COLUMNS:")
for col in df.columns:
    print("-", col)

print()
print(df.head())


(df.head(20)
 .to_json(
     out / "sample_preview.json",
     orient="records",
     indent=2,
     force_ascii=False
 ))