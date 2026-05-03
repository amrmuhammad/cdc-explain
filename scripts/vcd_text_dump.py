import sys

def parse_vcd_header(filepath):
    """Extract signal definitions from the VCD header."""
    with open(filepath) as f:
        lines = f.readlines()
    
    # Find the section that maps identifier codes to signal names
    id_map = {}  # code -> full_name
    stack = []   # scope hierarchy tracker
    collecting = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("$var"):
            # $var wire 1 & clk_write $end
            parts = line.split()
            # parts: ['$var', 'wire', '1', '&', 'clk_write', '$end']
            if len(parts) >= 5:
                code = parts[3]
                name = parts[4].split('[')[0]   # strip vector width brackets
                full_name = ".".join(stack + [name])
                id_map[code] = full_name
        elif line.startswith("$scope"):
            # $scope module TOP $end
            module_name = line.split()[2]
            stack.append(module_name)
        elif line == "$upscope $end":
            if stack:
                stack.pop()
        elif line == "$enddefinitions $end":
            break
    
    return id_map

def dump_signals(vcd_file, watch_signals):
    id_map = parse_vcd_header(vcd_file)
    # Invert: full_name -> code
    name_to_code = {name: code for code, name in id_map.items()}
    
    # Find codes for the signals we want to watch (by matching substring in full name)
    codes_to_watch = set()
    for sig in watch_signals:
        for code, full_name in id_map.items():
            if sig in full_name:   # simple substring match
                codes_to_watch.add(code)
    
    with open(vcd_file) as f:
        lines = f.readlines()
    
    in_value_section = False
    time_val = 0
    for line in lines:
        line = line.strip()
        if line.startswith("$enddefinitions"):
            in_value_section = True
            continue
        if not in_value_section:
            continue
        if line.startswith("#"):
            time_val = int(line[1:])
        elif line.startswith("0") or line.startswith("1"):
            # scalar value change: format '1&' or '0&'
            if len(line) >= 2 and line[1] in codes_to_watch:
                code = line[1]
                val = line[0]
                print(f"t={time_val:>5d} ps  {id_map.get(code, code):40s} -> {val}")
        elif line.startswith("b") and '"' in line:
            # vector change: e.g., 'b00010 "'
            code = line.split()[-1].strip('"')
            if code in codes_to_watch:
                val = line.split()[0][1:]   # strip leading 'b'
                print(f"t={time_val:>5d} ps  {id_map.get(code, code):40s} -> {val}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/vcd_text_dump.py <vcd_file>")
        sys.exit(1)
    # Watch these internal signals (substrings of full hierarchical names)
    watch = [
        "clk_write",
        "clk_read",
        "wr_en",
        "wr_en_sync",
        "empty",
        "rd_data"
    ]
    dump_signals(sys.argv[1], watch)
