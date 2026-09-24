from pathlib import Path
import json

from backend.services.eea_station_data_loader import load_metadata_rows


def test_metadata_loader(tmp_path):
    file = tmp_path/"stations.json"
    file.write_text(
        json.dumps([{"id":1}]),
        encoding="utf-8"
    )

    result = load_metadata_rows(file)

    assert result[0]["id"] == 1
