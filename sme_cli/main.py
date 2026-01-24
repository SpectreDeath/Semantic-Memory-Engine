import click
import os
import sys
import psutil
import sqlite3
from colorama import Fore, Style, init

# Initialize colors for Windows
init(autoreset=True)
sys.path.append(os.getcwd())

@click.group()
def cli():
    """SME: Semantic Memory Engine & Forensic Toolkit"""
    pass

@cli.command()
def verify():
    """Forensic Health Check: Data & Hardware."""
    click.secho("\n🔍 [SME SYSTEM DIAGNOSTICS]", fg='cyan', bold=True)
    
    # 1. Hardware Status
    mem = psutil.virtual_memory()
    cpu_load = psutil.cpu_percent()
    click.echo(f"{Fore.YELLOW}RAM Usage: {Fore.WHITE}{mem.percent}% ({mem.used/1e9:.1f}GB / {mem.total/1e9:.1f}GB)")
    click.echo(f"{Fore.YELLOW}CPU Load:  {Fore.WHITE}{cpu_load}%")

    # 2. Data Integrity
    click.echo(f"\n{Fore.CYAN}--- Data Integrity ---")
    paths = {
        "Knowledge DB": "data/knowledge_core.sqlite",
        "Assertions": "data/conceptnet-assertions-5.7.0.csv"
    }
    
    for name, path in paths.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1e9
            click.echo(f" ✅ {Fore.GREEN}{name:.<15} {Fore.WHITE}{path} ({size:.2f} GB)")
            
            # If it's the DB, check table count
            if path.endswith(".sqlite") and size > 0:
                try:
                    conn = sqlite3.connect(path)
                    count = conn.execute("SELECT count(*) FROM assertions").fetchone()[0]
                    click.echo(f"    └─ Record Count: {count:,} relations")
                    conn.close()
                except Exception as e:
                    click.echo(f"    └─ ⚠️ Record Count Error: {e}")
        else:
            click.echo(f" ❌ {Fore.RED}{name:.<15} {Fore.WHITE}MISSING")

@cli.command()
def index():
    """Execute Reasoning Quantizer Distillation."""
    click.secho("\n🧠 [INITIATING KNOWLEDGE DISTILLATION]", fg='magenta', bold=True)
    from src.logic.reasoning_quantizer import ReasoningQuantizer
    
    csv_path = "data/conceptnet-assertions-5.7.0.csv"
    if not os.path.exists(csv_path):
        click.secho(f"🛑 Error: {csv_path} not found!", fg='red')
        return
        
    quantizer = ReasoningQuantizer()
    quantizer.distill_assertions(csv_path)

if __name__ == "__main__":
    cli()
