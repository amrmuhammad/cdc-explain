// BUG-002: Guaranteed CDC failure – pulse crossing without synchronizer
module top (
    input  wire clk_fast,
    input  wire pulse_in,    // Single‑cycle pulse in fast domain
    input  wire clk_slow,
    output wire flag_out     // Should become 1 after pulse detected
);
    // 2‑FF synchronizer for the pulse (NO stretching)
    reg [1:0] sync_ff;
    always @(posedge clk_slow) begin
        sync_ff <= {sync_ff[0], pulse_in};
    end

    // Sticky flag: becomes 1 when synchronized pulse is seen
    reg flag;
    always @(posedge clk_slow) begin
        if (sync_ff[1])
            flag <= 1'b1;
        else
            flag <= flag;
    end
    assign flag_out = flag;
endmodule
