from engine.log_parser import extract_failure
from engine.cdc_ingestor import load_cdc_violations
from engine.vcd_reader import get_signal_timeline
from engine.prompt_builder import build_prompt
from openai import OpenAI

SIGNALS_OF_INTEREST = [
    "TOP.dual_clock_fifo.clk_write",
    "TOP.dual_clock_fifo.clk_read",
    "TOP.dual_clock_fifo.wr_en",
    "TOP.dual_clock_fifo.wr_en_sync",
    "TOP.dual_clock_fifo.empty",
    "TOP.dual_clock_fifo.rd_data[7:0]",
    "TOP.dual_clock_fifo.wr_ack",
]

def run_explanation(log_path, vcd_path, cdc_path, llm_client=None, dry_run=False):
    with open(log_path, "r") as f:
        failure = extract_failure(f.read())
    if not failure:
        return "No simulation failure found in log."

    cdc_violations = load_cdc_violations(cdc_path)

    # Get timeline of all relevant signal changes (no time filter for now)
    timeline = get_signal_timeline(vcd_path, SIGNALS_OF_INTEREST)

    prompt = build_prompt(failure, timeline, cdc_violations)

    if dry_run:
        return prompt

    # Use Ollama local endpoint
    if llm_client is None:
        llm_client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )

    response = llm_client.chat.completions.create(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content
