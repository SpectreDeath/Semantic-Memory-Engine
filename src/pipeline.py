# =============================================================================
# SME Pipeline - Main Orchestration
# =============================================================================
# Refactored to use modular tasks from src/orchestration/tasks/
# =============================================================================

import sys
import os
from prefect import task, flow, get_run_logger

# Add the project root to sys.path to allow imports from tests and src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import extracted tasks modules
from src.orchestration.tasks import (
    run_rss_bridge,
    run_scholar_api,
    run_osint_scan,
    stream_bipartite,
    extract_targets,
    run_forensic_summary,
)


@task(name="Verify Forensic Stack")
def verify_stack():
    """Run the forensic stack verification logic."""
    logger = get_run_logger()
    logger.info("Starting forensic stack verification...")
    from tests.verify_forensic_stack import main as run_verification
    exit_code = run_verification()
    return exit_code == 0


@flow(name="SME Pivot and Search Operational Flow")
def s_m_e_full_intel_run():
    """Automated intelligence gathering pipeline."""
    logger = get_run_logger()
    logger.info("SME Intelligence Run Initiated")
    
    # 1. Health Check
    if not verify_stack():
        logger.error("System Unhealthy. Aborting Intel Run.")
        return

    # 2. Macro Ingestion
    run_rss_bridge()
    run_scholar_api()
    
    # 3. Pivot & Scan
    targets = extract_targets()
    osint_hits = []
    if targets:
        osint_hits = run_osint_scan.map(targets)
        # Bipartite streaming
        stream_bipartite(osint_hits)
    
    # 4. Agentic Intelligence & Alerts
    # Load raw data for packaging
    from src.utils.loaders import load_intel_data
    intel_package = {
        "osint": load_intel_data("data/raw/osint_results.json"),
        "news": load_intel_data("data/raw/forensic_news.json")
    }
    
    # Trigger Brain (Langflow Simulation/Runtime)
    run_forensic_summary(intel_package)
    
    # Trigger Active Defense Alerts
    try:
        from src.utils.alerts import check_for_threat_collision
        check_for_threat_collision(intel_package)
    except Exception as e:
        logger.warning(f"Alert System Error: {e}")
    
    logger.info("✅ SME Intelligence Run Complete.")


if __name__ == "__main__":
    s_m_e_full_intel_run()
