#include <verilated.h>
#include <verilated_vcd_c.h>
#include "Vfifo_rtl.h"
#include <cstdio>

// Half‑periods for fast (write) and slow (read) clocks
#define FAST_HALF  5
#define SLOW_HALF 15

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vfifo_rtl *top = new Vfifo_rtl;

    // Tracing setup
    Verilated::traceEverOn(true);
    VerilatedVcdC *tfp = new VerilatedVcdC;
    top->trace(tfp, 99);
    tfp->open("dump.vcd");

    vluint64_t sim_time = 0;
    int fail = 0;

    printf("Simulation started.\n");
    fflush(stdout);

    // Reset
    top->rst_n = 0;
    top->wr_en = 0;
    top->rd_en = 0;
    for (int i = 0; i < 8; i++) {
        top->clk_write = 0;
        top->clk_read  = 0;
        top->eval(); tfp->dump(sim_time++);
        top->clk_write = 1;
        top->eval(); tfp->dump(sim_time++);
        top->clk_read  = 1;
        top->eval(); tfp->dump(sim_time++);
    }
    top->rst_n = 1;

    // Write two known values
    top->wr_en   = 1;
    top->wr_data = 0xAA;
    for (int i = 0; i < 2; i++) {
        top->clk_write = 0; top->eval(); tfp->dump(sim_time++);
        top->clk_write = 1; top->eval(); tfp->dump(sim_time++);
    }
    top->wr_en = 0;

    top->wr_en   = 1;
    top->wr_data = 0xBB;
    for (int i = 0; i < 2; i++) {
        top->clk_write = 0; top->eval(); tfp->dump(sim_time++);
        top->clk_write = 1; top->eval(); tfp->dump(sim_time++);
    }
    top->wr_en = 0;

    // Read back on the slow clock: expect 0xAA then 0xBB
    top->rd_en = 1;    // keep read enable asserted

    bool first_read  = false;
    bool second_read = false;
    int  timeout     = 0;
    while (!first_read || !second_read) {
        top->clk_read = 0; top->eval(); tfp->dump(sim_time++);
        top->clk_read = 1; top->eval(); tfp->dump(sim_time++);

        // Check on rising edge
        if (!top->empty) {
            if (!first_read) {
                if (top->rd_data == 0xAA) {
                    printf("Read first byte: 0x%02x at time %" PRIu64 " ns\n", top->rd_data, sim_time);
                    fflush(stdout);
                    first_read = true;
                } else {
                    printf("FAILURE at time %" PRIu64 " ns: expected 0xAA, got 0x%02x\n",
                           sim_time, top->rd_data);
                    fflush(stdout);
                    fail = 1;
                    break;
                }
            } else {
                if (top->rd_data == 0xBB) {
                    printf("Read second byte: 0x%02x at time %" PRIu64 " ns\n", top->rd_data, sim_time);
                    fflush(stdout);
                    second_read = true;
                } else {
                    printf("FAILURE at time %" PRIu64 " ns: expected 0xBB, got 0x%02x\n",
                           sim_time, top->rd_data);
                    fflush(stdout);
                    fail = 1;
                    break;
                }
            }
        }

        // Timeout after 500 cycles (adjust as needed)
        if (++timeout > 500) {
            printf("FAILURE: timeout waiting for %s byte\n",
                   first_read ? "second" : "first");
            fflush(stdout);
            fail = 1;
            break;
        }
    }

    tfp->close();
    delete top;
    return fail;
}
