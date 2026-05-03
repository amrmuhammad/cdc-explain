from vcdvcd import VCDVCD
from typing import Dict, List

def get_final_signal_values(vcd_path: str, signals: List[str]) -> Dict[str, str]:
    vcd = VCDVCD(vcd_path)
    result = {}
    for sig in signals:
        try:
            values = vcd[sig]
            result[sig] = values[-1] if values else "unknown"
        except KeyError:
            result[sig] = "signal not found"
    return result
