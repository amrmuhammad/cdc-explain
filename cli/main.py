import click
from engine.explainer import run_explanation

@click.command()
@click.option("--log", required=True, help="Path to simulation log")
@click.option("--vcd", required=True, help="Path to VCD waveform dump")
@click.option("--cdc", required=True, help="Path to CDC violations JSON")
@click.option("--dry-run", is_flag=True, help="Print the LLM prompt, do not call API")
def explain(log, vcd, cdc, dry_run):
    result = run_explanation(log_path=log, vcd_path=vcd, cdc_path=cdc, dry_run=dry_run)
    click.echo(result)

if __name__ == "__main__":
    explain()
