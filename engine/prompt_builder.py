from typing import Dict, List, Tuple

def build_prompt(failure: Dict,
                 timeline: List[Tuple[int, str, str]],
                 cdc_violations: List[Dict]) -> str:
    """
    Construct an evidence-rich prompt for CDC root cause analysis.
    """
    # Build a compact timeline string
    timeline_str = ""
    max_events = 80  # Limit to avoid token overflow
    for i, (t, sig, val) in enumerate(timeline[:max_events]):
        timeline_str += f"{t:>8} ps  {sig:45s} -> {val}\n"
    if len(timeline) > max_events:
        timeline_str += f"... (truncated, total {len(timeline)} events)\n"

    # Describe the violation
    vios_str = ""
    for i, v in enumerate(cdc_violations, 1):
        vios_str += f"""
Violation {i}:
  Source signal:       {v.get('source_signal', 'unknown')}
  Source clock:        {v.get('source_clock', 'unknown')}
  Destination signal:  {v.get('destination_signal', 'unknown')}
  Destination clock:   {v.get('destination_clock', 'unknown')}
  Type:                {v.get('violation_type', 'unknown')}
  Description:         {v.get('description', 'none')}
  Recommendation:      {v.get('recommendation', 'none')}
"""

    # --- The new system message and few-shot example ---
    system_message = """You are a hardware verification engineer analyzing a clock domain crossing (CDC) failure.
You MUST follow these rules:
1. Base every claim on the provided simulation timeline (the exact signal names, values, and times).
2. Quote the specific timestamp and signal value that supports each point.
3. If the evidence is insufficient, say so instead of guessing.
4. Do not invent internal states or behaviors not shown in the trace.
5. Structure your answer: (a) Observed behavior, (b) Root cause linked to CDC violation, (c) Why the failure symptom occurred, (d) Recommendation.

Example of a good answer:
---
Observed behavior:
- At 24 ps, wr_en rises (->1) and stays high until 32 ps.
- wr_en_sync remains 0 throughout the entire trace.
- empty stays 1, never dropping to 0.
- The simulation log reports a timeout waiting for the first byte.

Root cause:
The CDC rule violation is a missing pulse synchronizer on wr_en crossing from clk_write to clk_read. Because wr_en is only a single-cycle pulse on the fast clock, the 2-FF synchronizer (wr_sync_ff) cannot capture the pulse in the slow clock domain. As a result, wr_en_sync never becomes 1.

Why the timeout occurred:
The FIFO's empty flag is driven by !wr_ack, which itself depends on wr_en_sync. Since wr_en_sync stays 0, empty stays 1, and the read side never sees data. The testbench waiting for empty -> 0 times out.

Recommendation:
Implement a pulse synchronizer (toggle synchronizer) or a handshake protocol on the wr_en crossing to ensure every write pulse is detected in the clk_read domain.
---

Now analyze the following failure. Use the timeline and the CDC violation description.
"""

    prompt = f"""{system_message}

### Simulation Failure
- Message: {failure.get('message', 'No details')}

### Signal Timeline (relevant events)
{timeline_str}

### CDC Violations
{vios_str}

### Task
Based **only on the provided timeline and violation**, explain the failure.
"""
    return prompt
