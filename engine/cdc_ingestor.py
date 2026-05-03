import json
from typing import List, Dict

def load_cdc_violations(json_path: str) -> List[Dict]:
    with open(json_path, "r") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]
