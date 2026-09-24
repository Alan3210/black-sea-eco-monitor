from pathlib import Path
import pandas as pd

def parse_eea_measurements(parquet_path):
    df=pd.read_parquet(parquet_path)
    result=[]
    for _, row in df.iterrows():
        result.append({
            "samplingpoint": row.get("Samplingpoint"),
            "pollutant_code": row.get("Pollutant"),
            "observed_at": row.get("Start"),
            "observed_end": row.get("End"),
            "value": row.get("Value"),
            "unit": row.get("Unit"),
            "verification": row.get("Verification"),
        })
    return result
