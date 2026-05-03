// ============================================================================
// dual_clock_fifo – A minimal asynchronous FIFO with a DELIBERATE CDC bug.
// This module is designed to fail in simulation and demonstrate the need for
// proper clock domain crossing techniques.
//
// Written for the "cdc-explain" open‑source project.
// License: MIT (see project root)
// ============================================================================

// A module is the basic building block in Verilog, like a class in software.
// Here we define "dual_clock_fifo" and its interface (ports).
// Parameters allow the user to change the data width and FIFO depth when
// they instantiate the module. #(parameter ...) creates a compile‑time constant.
module dual_clock_fifo #(
    parameter WIDTH = 8,    // number of bits in each data word
    parameter DEPTH = 4     // how many words the FIFO can hold
) (
    // ---- Ports: the external connections of this module ----
    // input wire ...  – signals that come INTO the module
    // output wire ... – signals that go OUT of the module
    input  wire             clk_write,   // clock for the write side (fast)
    input  wire             clk_read,    // clock for the read side (slow)
    input  wire             rst_n,       // asynchronous reset (active low)

    input  wire             wr_en,       // write‑enable pulse, 1 cycle on clk_write
    input  wire [WIDTH-1:0] wr_data,     // data to be written (WIDTH bits)
    input  wire             rd_en,       // read‑enable, active on clk_read
    output wire [WIDTH-1:0] rd_data,     // data that is read out
    output wire             empty,       // 1 when the FIFO is empty
    output wire             full         // 1 when the FIFO is full
);

    // ---- Internal regs and wires ----
    // 'reg' is a variable that holds its value until assigned again (like a flip‑flop).
    // 'wire' is just a continuous connection (combinational logic).
    // $clog2(DEPTH) computes the number of bits needed to represent values 0..DEPTH-1.
    // We add an extra bit to distinguish full vs. empty (common trick).

    // The actual memory array: DEPTH words, each WIDTH bits wide.
    // 'reg [WIDTH-1:0]' means each element is a WIDTH‑bit register.
    reg [WIDTH-1:0] mem [0:DEPTH-1];

    // Pointers for write and read. The extra MSB helps detect full/empty.
    reg [$clog2(DEPTH):0] wr_ptr, rd_ptr;

    // Signals that cross between clock domains.
    // These will be driven by synchronisers (which contain the bug).
    wire wr_en_sync;   // wr_en after synchronisation to clk_read domain
    wire rd_en_sync;   // rd_en after synchronisation to clk_write domain (unused here)

    // ---- Write side (clk_write domain) ----
    // 'always @(posedge clk_write or negedge rst_n)' means:
    //   Execute this block whenever clk_write rises (posedge) OR rst_n falls (negedge).
    //   This is how you describe an asynchronous reset flip‑flop in Verilog.
    always @(posedge clk_write or negedge rst_n) begin
        if (!rst_n) begin
            // When reset is active (low), set the pointer back to 0.
            // '<= ' is a non‑blocking assignment. It schedules the update for the end
            // of the current time step, avoiding race conditions between always blocks.
            wr_ptr <= 0;
        end else if (wr_en && !full) begin
            // Write condition: a write is requested AND the FIFO is not full.
            // The memory is indexed with the lower bits of the pointer
            // (the extra MSB is used only for full/empty logic).
            mem[wr_ptr[$clog2(DEPTH)-1:0]] <= wr_data;
            // Increment the write pointer.
            wr_ptr <= wr_ptr + 1;
        end
    end

    // ---- Read side (clk_read domain) ----
    always @(posedge clk_read or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= 0;
        end else if (rd_en && !empty) begin
            rd_ptr <= rd_ptr + 1;
        end
    end

    // ****************** CDC BUG STARTS HERE ******************
    // The signal 'wr_en' is a single‑cycle pulse on clk_write.
    // To pass it to clk_read safely we MUST stretch the pulse (or use a handshake)
    // so the slower clock can capture it. Instead, we use a simple 2‑flop
    // synchroniser, which only prevents metastability but does NOT guarantee all
    // pulses are seen. The pulse can be missed if it occurs when clk_read is not
    // sampling, leading to lost writes and data corruption.
    // *********************************************************

    // Two‑flop synchroniser for wr_en crossing from clk_write to clk_read.
    // This block is in the clk_read domain.
    reg [1:0] wr_sync_ff;   // 2‑bit shift register (synchroniser chain)
    always @(posedge clk_read or negedge rst_n) begin
        if (!rst_n) begin
            wr_sync_ff <= 2'b00;   // both flip‑flops reset to 0
        end else begin
            // Shift the chain right and load the new value (wr_en) into the first flop.
            // This is JUST a synchroniser; it does NOT stretch the pulse.
            wr_sync_ff <= {wr_sync_ff[0], wr_en};
        end
    end
    assign wr_en_sync = wr_sync_ff[1];  // the output of the second flop is 'synchronised'

    // The bug: because wr_en is only active for one clk_write cycle, and clk_read is
    // slower, wr_en_sync may never become 1, or become a sub‑sampled glitch.

    // ****************** CDC BUG ENDS HERE ******************

    // A simple flag to indicate that a write was acknowledged on the read side.
    // Used to help with empty/full logic.
    reg wr_ack;
    always @(posedge clk_read or negedge rst_n) begin
        if (!rst_n) wr_ack <= 0;
        else         wr_ack <= wr_en_sync;   // just latch the synchronised write enable
    end

    // ---- Empty / Full logic ----
    // A common simple async FIFO uses Gray‑code pointers, but here we use a plain
    // binary approach with an extra MSB and the wr_ack flag.
    assign empty = !wr_ack;
    assign full  = (wr_ptr[$clog2(DEPTH)-1:0] == rd_ptr[$clog2(DEPTH)-1:0])
                   && (wr_ptr[$clog2(DEPTH)] != rd_ptr[$clog2(DEPTH)]);

    // ---- Read data output ----
    // Combinational read: the data appears on rd_data whenever the address changes.
    // In a real design we would register it, but this keeps the example simple.
    assign rd_data = mem[rd_ptr[$clog2(DEPTH)-1:0]];

endmodule
