from typing import List, Dict, Tuple, Optional

def _parse_vcd_header(filepath):
    """Map VCD identifier codes to hierarchical signal names."""
    id_map = {}
    stack = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line.startswith("$var"):
                # $var wire 1 & clk_write $end
                parts = line.split()
                if len(parts) >= 5:
                    code = parts[3]
                    name = parts[4].split('[')[0]   # strip vector width brackets
                    full_name = ".".join(stack + [name])
                    id_map[code] = full_name
            elif line.startswith("$scope"):
                module_name = line.split()[2]
                stack.append(module_name)
            elif line == "$upscope $end":
                if stack:
                    stack.pop()
            elif line == "$enddefinitions $end":
                break
    return id_map

def get_final_signal_values(vcd_path: str, signals: List[str]) -> Dict[str, str]:
    """Return final value of each named signal from the VCD file."""
    id_map = _parse_vcd_header(vcd_path)
    name_to_code = {name: code for code, name in id_map.items()}
    # read values section line by line, tracking last time and values
    current_values = {}
    in_value_section = False
    with open(vcd_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("$enddefinitions"):
                in_value_section = True
            elif not in_value_section:
                continue
            elif line.startswith("#"):
                # timestamp, ignore for final snapshot
                pass
            elif line.startswith("0") or line.startswith("1"):
                # scalar change: '1&' or '0&'
                if len(line) >= 2 and line[1] in id_map:
                    code = line[1]
                    val = line[0]
                    current_values[code] = val
            elif line.startswith("b") and '"' in line:
                # vector change: 'b00010 "'
                code = line.split()[-1].strip('"')
                if code in id_map:
                    val = line.split()[0][1:]   # strip 'b'
                    current_values[code] = val
    # map back to signal names
    result = {}
    for sig in signals:
        code = name_to_code.get(sig)
        if code and code in current_values:
            result[sig] = current_values[code]
        else:
            result[sig] = "unknown"
    return result

def get_signal_timeline(vcd_path: str, signals: List[str],
                        start_time: Optional[int] = None,
                        end_time: Optional[int] = None) -> List[Tuple[int, str, str]]:
    """
    Return a sorted list of (time_ps, signal_name, value) for any change
    of the given signals within the optional time window.
    """
    id_map = _parse_vcd_header(vcd_path)
    name_to_code = {name: code for code, name in id_map.items()}
    codes_to_watch = set()
    for sig in signals:
        code = name_to_code.get(sig)
        if code:
            codes_to_watch.add(code)

    events = []
    current_values = {}
    in_value_section = False
    current_time = 0
    with open(vcd_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("$enddefinitions"):
                in_value_section = True
                continue
            if not in_value_section:
                continue
            if line.startswith("#"):
                current_time = int(line[1:])
            elif line.startswith("0") or line.startswith("1"):
                if len(line) >= 2 and line[1] in codes_to_watch:
                    code = line[1]
                    val = line[0]
                    if current_values.get(code) != val:
                        current_values[code] = val
                        if (start_time is None or current_time >= start_time) and \
                           (end_time is None or current_time <= end_time):
                            events.append((current_time, id_map[code], val))
            elif line.startswith("b") and '"' in line:
                code = line.split()[-1].strip('"')
                if code in codes_to_watch:
                    val = line.split()[0][1:]   # strip 'b'
                    if current_values.get(code) != val:
                        current_values[code] = val
                        if (start_time is None or current_time >= start_time) and \
                           (end_time is None or current_time <= end_time):
                            events.append((current_time, id_map[code], val))

    events.sort(key=lambda x: x[0])
    return events
