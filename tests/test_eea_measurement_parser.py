import pandas as pd
from backend.services.eea_measurement_parser import parse_eea_measurements

def test_parse_eea_measurements(tmp_path):
    p=tmp_path/"sample.parquet"
    pd.DataFrame([{
        "Samplingpoint":"BG/SPO-TEST",
        "Pollutant":5,
        "Start":"2026-01-01 00:00:00",
        "End":"2026-01-01 01:00:00",
        "Value":12.5,
        "Unit":"ug.m-3",
        "Verification":1,
    }]).to_parquet(p)

    r=parse_eea_measurements(p)
    assert r[0]["value"]==12.5
