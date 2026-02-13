import sys
import os
import json
from pathlib import Path
from prefect import task, flow, get_run_logger

# Add the project root to sys.path to allow imports from tests and src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@task(name="Verify Forensic Stack")
def verify_stack():
    """Run the forensic stack verification logic."""
    logger = get_run_logger()
    logger.info("Starting forensic stack verification...")
    from tests.verify_forensic_stack import main as run_verification
    exit_code = run_verification()
    return exit_code == 0

@task(name="Run RSS Bridge")
def run_rss_bridge():
    """Gather news via RSS Bridge and sync to Supabase."""
    logger = get_run_logger()
    logger.info("📡 Running RSS Bridge...")
    from src.gathering.rss_bridge import main as rss_main
    rss_main()
    
    # Sync to Supabase
    try:
        from src.database.supabase_client import sync_news_to_supabase
        from src.ui.dashboard import load_intel_data
        news = load_intel_data("data/raw/forensic_news.json")
        sync_news_to_supabase(news)
    except Exception as e:
        logger.warning(f"Supabase News Sync Failed: {e}")
        
    return True

@task(name="Run Scholar API")
def run_scholar_api():
    """Gather academic papers via Scholar API and sync to Supabase."""
    logger = get_run_logger()
    logger.info("🎓 Running Scholar API...")
    from src.gathering.scholar_api import main as scholar_main
    # Fetching a small sample for the pipeline run
    scholar_main()
    
    # Sync to Supabase
    try:
        from src.database.supabase_client import sync_research_to_supabase
        from src.ui.dashboard import load_intel_data
        research = load_intel_data("data/raw/research_papers.json")
        sync_research_to_supabase(research)
    except Exception as e:
        logger.warning(f"Supabase Research Sync Failed: {e}")
        
    return True

@task(name="Extract Targets from Research", persist_result=True)
def extract_targets():
    """Extract authors from research papers for OSINT pivoting."""
    logger = get_run_logger()
    path = Path("data/raw/research_papers.json")
    if not path.exists():
        logger.warning("No research papers found to pivot from.")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    
    # Extract candidate authors
    candidates = []
    for paper in papers:
        for author in paper.get("authors", []):
            # Basic cleanup: join names for username candidate
            clean_name = author.replace(" ", "")
            candidates.append(clean_name)
    
    # NLP Filtering Layer
    from src.utils.entity_filter import filter_targets
    targets = filter_targets(candidates)
    
    logger.info(f"🔍 Filtered {len(candidates)} candidates down to {len(targets)} high-probability targets.")
    return targets[:5] # Limit for the operational run

@task(name="Run OSINT Toolkit")
def run_osint_scan(username):
    """Run OSINT footprinting for a specific target."""
    logger = get_run_logger()
    logger.info(f"🕵️ Scanning footprint for: {username}")
    from src.gathering.osint_toolkit import footprint_username, save_to_json
    results = footprint_username(username)
    save_to_json(results)
    return results

@task(name="Stream to Gephi Bipartite")
def stream_bipartite(osint_results_list):
    """Stream OSINT results to Gephi as a bipartite graph."""
    logger = get_run_logger()
    logger.info("📊 Streaming bipartite footprint to Gephi...")
    from src.utils.gephi_bridge import connect_to_gephi, graph
    
    gephi, connected = connect_to_gephi()
    if not connected:
        logger.warning("Gephi not available. Skipping stream.")
        return
        
    for res in osint_results_list:
        user_node = graph.Node(res["username"], Type="Actor", Color="Orange")
        gephi.add_node(user_node)
        
        for platform in res.get("platforms", []):
            if platform["status"] == "found":
                plat_node = graph.Node(platform["name"], Type="Platform", Color="Blue")
                gephi.add_node(plat_node)
                gephi.add_edge(graph.Edge(user_node, plat_node, Type="Found_On"))
    
    logger.info("Gephi bipartite streaming complete.")

@task(name="Generate Forensic Summary")
def run_forensic_summary(intel_package):
    """Generate agentic summary using Langflow."""
    logger = get_run_logger()
    logger.info("Generating Agentic Forensic Summary...")
    try:
        from src.ai.agent_logic import generate_forensic_summary
        summary = generate_forensic_summary(intel_package)
        logger.info("Summary Generated")
        return summary
    except Exception as e:
        logger.warning(f"Forensic Summary Failed: {e}")
        return "Summary unavailable."

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
