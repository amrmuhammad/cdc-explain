import re
from typing import Optional, Dict

def extract_failure(log_text: str) -> Optional[Dict]:
    patterns = [
        r"FAILURE:\s*(?P<message>.*)",
        r"FAILURE at time\s+(?P<time_ns>\d+)\s*ns:\s*(?P<message>.*)",
    ]
    for pat in patterns:
        match = re.search(pat, log_text, re.IGNORECASE)
        if match:
            result = {"message": match.group("message").strip()}
            result["time_ns"] = int(match.group("time_ns")) if match.groupdict().get("time_ns") else None
            return result
    return None
