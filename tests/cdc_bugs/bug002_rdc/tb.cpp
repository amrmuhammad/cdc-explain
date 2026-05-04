#include <verilated.h>
#include <verilated_vcd_c.h>
#include "Vtop.h"
#include <cstdio>

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    Vtop *top = new Vtop;

    Verilated::traceEverOn(true);
    VerilatedVcdC *tfp = new VerilatedVcdC;
    top->trace(tfp, 99);
    tfp->open("dump.vcd");

    vluint64_t sim_time = 0;
    int fail = 0;
    printf("Simulation started.\n");
    fflush(stdout);

    // Initial values
    top->clk_fast = 0;
    top->pulse_in = 0;
    top->clk_slow = 0;
    top->eval(); tfp->dump(sim_time++);

    // 1. Advance slow clock a couple of cycles (no pulse)
    for (int i = 0; i < 4; i++) {
        top->clk_slow = 1;
        top->eval(); tfp->dump(sim_time++);
        top->clk_slow = 0;
        top->eval(); tfp->dump(sim_time++);
    }

    // 2. Inject a fast‑domain pulse that falls entirely between two
    //    rising edges of clk_slow.
    top->clk_fast = 1;
    top->pulse_in = 1;    // pulse starts
    top->eval(); tfp->dump(sim_time++);
    top->clk_fast = 0;
    top->pulse_in = 0;    // pulse ends after one fast cycle
    top->eval(); tfp->dump(sim_time++);

    // 3. Now let the slow clock rise again. The pulse is already gone.
    for (int i = 0; i < 20; i++) {
        top->clk_slow = 1;
        top->eval(); tfp->dump(sim_time++);
        top->clk_slow = 0;
        top->eval(); tfp->dump(sim_time++);
    }

    // 4. Check the flag
    if (top->flag_out == 0) {
        printf("FAILURE: flag_out never set – pulse missed due to missing synchronizer.\n");
        fflush(stdout);
        fail = 1;
    } else {
        printf("Flag set correctly.\n");
    }

    tfp->close();
    delete top;
    return fail;
}
