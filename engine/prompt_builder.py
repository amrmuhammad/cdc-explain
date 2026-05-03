from typing import Dict, List

def build_prompt(failure: Dict, final_signals: Dict[str, str],
                 cdc_violations: List[Dict]) -> str:
    prompt = f"""You are an expert RTL verification engineer specialised in clock domain crossing (CDC) analysis.
Given the following simulation failure and the associated CDC violations, explain step‑by‑step
how the structural CDC problem caused the observed timeout.

### Simulation Failure
- Message: {failure.get('message', 'No details')}

### Final Signal Values from Waveform
{chr(10).join(f"  {sig}: {val}" for sig, val in final_signals.items())}

### CDC Violations
"""
    for i, v in enumerate(cdc_violations, 1):
        prompt += f"""
Violation {i}:
  Source signal:       {v.get('source_signal', 'unknown')}
  Source clock:        {v.get('source_clock', 'unknown')}
  Destination signal:  {v.get('destination_signal', 'unknown')}
  Destination clock:   {v.get('destination_clock', 'unknown')}
  Type:                {v.get('violation_type', 'unknown')}
  Description:         {v.get('description', 'none')}
  Recommendation:      {v.get('recommendation', 'none')}
"""
    prompt += """
### Task
Based **only on the provided data**, explain the causal chain:
1. Why the CDC violation is functionally dangerous in this design.
2. How those structural issues caused the simulation to time out.
3. Which signals are affected and why the FIFO never becomes non‑empty.

Be precise, refer to signal names, and do not invent information not present.
"""
    return prompt
