import sys
from vcdvcd import VCDVCD

vcd = VCDVCD(sys.argv[1])

# Hierarchical signal names we care about (from your previous listing)
signals_of_interest = {
    'TOP.dual_clock_fifo.clk_write',
    'TOP.dual_clock_fifo.clk_read',
    'TOP.dual_clock_fifo.wr_en',
    'TOP.dual_clock_fifo.wr_en_sync',
    'TOP.dual_clock_fifo.empty',
    'TOP.dual_clock_fifo.rd_data[7:0]',
}

print("Time(ps)\tSignal\t\t\tValue")
print("-" * 50)
count = 0
for time_val, changes in vcd:
    for ref, val in changes:
        if ref in signals_of_interest:
            print(f"{time_val}\t{ref}\t{val}")
            count += 1
            if count >= 40:   # show first 40 relevant changes
                sys.exit(0)
