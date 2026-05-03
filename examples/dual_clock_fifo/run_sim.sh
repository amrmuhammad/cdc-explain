#!/bin/bash
set -e

# Step 1: Lint-only run to capture warnings (including CDC)
# We add `; true` so the exit code is always 0, even if warnings appear.
verilator --lint-only fifo_rtl.v -Wall 2>&1 | tee verilator_cdc.txt ; true

# Step 2: Compile and simulate in one shot using --build
verilator --cc --trace --exe --build fifo_rtl.v tb.cpp -o sim

# Step 3: Run the generated simulation executable
./obj_dir/sim 2>&1 | tee sim.log

echo "✅ Simulation done. VCD: dump.vcd, log: sim.log, CDC/lint report: verilator_cdc.txt"
