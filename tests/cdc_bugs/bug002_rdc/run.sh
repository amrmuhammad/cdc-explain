#!/bin/bash
set -e
verilator --lint-only top.v -Wall 2>&1 | tee verilator_cdc.txt ; true
verilator --cc --trace --exe --build top.v tb.cpp -o sim
./obj_dir/sim 2>&1 | tee sim.log
echo "Simulation done. VCD: dump.vcd, log: sim.log"
