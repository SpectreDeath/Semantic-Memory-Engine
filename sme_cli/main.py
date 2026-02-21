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
@click.option('--force', is_flag=True, help="Force re-indexing even if data is current.")
def index(force):
    """Execute Smart Indexing with Data Lineage."""
    from src.logic.manifest_manager import ManifestManager
    from src.logic.reasoning_quantizer import ReasoningQuantizer
    
    mm = ManifestManager()
    quantizer = ReasoningQuantizer()
    csv_path = "data/conceptnet-assertions-5.7.0.csv"

    # Check for file existence first
    if not os.path.exists(csv_path):
        click.secho(f"❌ Error: {csv_path} not found!", fg='red')
        return

    # Lineage Check (The Colin Philosophy)
    if not mm.is_stale(csv_path) and not force:
        click.secho("✨ Data lineage is current. Skipping heavy distillation.", fg='green')
        click.echo("Use --force to override.")
        return

    click.secho("🧠 Hash mismatch or --force detected. Starting distillation...", fg='yellow')
    
    # Run the existing distillation logic
    quantizer.distill_assertions(csv_path)
    
    # Update the manifest so we remember this version
    mm.update_source(csv_path)
    click.secho("✅ Indexing complete and manifest updated.", fg='green')

@cli.command()
@click.option('--claims', '-c', type=click.Path(exists=True), default=None,
              help='Path to JSON file with claims. Format: [{"subject": "X", "predicate": "is", "object": "Y"}, ...]')
@click.option('--inline', '-i', default=None,
              help='Inline JSON array of claims (alternative to --claims file)')
def drift(claims, inline):
    """Compare claims against the HDF5 knowledge core (drift analysis)."""
    import json
    try:
        from src.logic.audit_engine import AuditEngine
    except ImportError as e:
        if 'h5py' in str(e):
            click.secho("❌ h5py required. Install with: pip install h5py", fg='red')
        else:
            click.secho(f"❌ Import error: {e}", fg='red')
        return

    if claims and inline:
        click.secho("❌ Use either --claims or --inline, not both.", fg='red')
        return
    if not claims and not inline:
        click.secho("Provide claims via --claims path/to.json or --inline '[{\"subject\":\"A\",\"predicate\":\"is\",\"object\":\"B\"}]'", fg='yellow')
        return

    try:
        if claims:
            with open(claims, 'r') as f:
                claims_list = json.load(f)
        else:
            # Handle inline JSON with proper escaping
            claims_list = json.loads(inline)
        if not isinstance(claims_list, list):
            claims_list = [claims_list]
    except (json.JSONDecodeError, TypeError) as e:
        click.secho(f"❌ Invalid JSON: {e}", fg='red')
        click.secho("Example usage: --inline '[{\"subject\":\"FastMCP\",\"predicate\":\"is\",\"object\":\"plumbing\"}]'", fg='yellow')
        return

    engine = AuditEngine()
    result = engine.analyze_drift(claims_list)
    drift_score = result["drift_score"]
    verified = result["verified"]
    anomalies = result["anomalies"]

    click.secho(f"\n📊 [DRIFT ANALYSIS]", fg='cyan', bold=True)
    click.echo(f"  Drift Score: {drift_score:.2%} ({len(anomalies)} anomalies / {len(claims_list)} claims)")
    if verified:
        click.echo(f"\n  ✅ Verified ({len(verified)}):")
        for c in verified[:5]:
            click.echo(f"     - {c.get('subject', '?')} {c.get('predicate', '?')} {c.get('object', '?')}")
        if len(verified) > 5:
            click.echo(f"     ... and {len(verified) - 5} more")
    if anomalies:
        click.echo(f"\n  ⚠️  Anomalies ({len(anomalies)}):")
        for c in anomalies[:5]:
            click.echo(f"     - {c.get('subject', '?')} {c.get('predicate', '?')} {c.get('object', '?')}")
        if len(anomalies) > 5:
            click.echo(f"     ... and {len(anomalies) - 5} more")
    if not verified and not anomalies:
        click.echo("  (No claims processed)")
    click.echo()

@cli.command()
def status():
    """Display SME Workstation Health and Data Lineage."""
    import psutil
    from src.logic.manifest_manager import ManifestManager
    import h5py
    import os

    mm = ManifestManager()
    
    # --- Hardware Telemetry ---
    ram = psutil.virtual_memory()
    click.secho(f"🖥️  Workstation: 32GB RAM ({ram.percent}% Used) | GTX 1660 Ti", fg='cyan', bold=True)

    # --- Lineage Manifest ---
    click.echo("\n📋 Data Lineage:")
    if not mm.data["sources"]:
        click.echo("  No data sources tracked in manifest.")
    for path, info in mm.data["sources"].items():
        name = os.path.basename(path)
        click.echo(f"  - {name}: {info['timestamp']} (Hash: {info['hash'][:8]}...)")

    # --- HDF5 Index Health ---
    h5_path = "data/knowledge_core.h5"
    if os.path.exists(h5_path):
        with h5py.File(h5_path, 'r') as f:
            size_gb = os.path.getsize(h5_path) / (1024**3)
            click.echo(f"\n🧠 Knowledge Core (HDF5):")
            click.echo(f"  - File: {h5_path} ({size_gb:.2f} GB)")
            click.echo(f"  - Keys: {list(f.keys())}")
    else:
        click.secho("\n⚠️  Knowledge Core (HDF5) not found. Run 'sme index' to build.", fg='yellow')

if __name__ == "__main__":
    cli()
