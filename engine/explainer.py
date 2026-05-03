from engine.log_parser import extract_failure
from engine.cdc_ingestor import load_cdc_violations
from engine.vcd_reader import get_final_signal_values
from engine.prompt_builder import build_prompt

SIGNALS_OF_INTEREST = [
    "TOP.dual_clock_fifo.clk_write",
    "TOP.dual_clock_fifo.clk_read",
    "TOP.dual_clock_fifo.wr_en",
    "TOP.dual_clock_fifo.wr_en_sync",
    "TOP.dual_clock_fifo.empty",
    "TOP.dual_clock_fifo.rd_data[7:0]",
]

def run_explanation(log_path, vcd_path, cdc_path, llm_client=None, dry_run=False):
    with open(log_path, "r") as f:
        failure = extract_failure(f.read())
    if not failure:
        return "No simulation failure found in log."

    cdc_violations = load_cdc_violations(cdc_path)
    final_signals = get_final_signal_values(vcd_path, SIGNALS_OF_INTEREST)
    prompt = build_prompt(failure, final_signals, cdc_violations)

    if dry_run or llm_client is None:
        return prompt

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content
