# =============================================================================
# Scholar Tasks
# =============================================================================
# Gather academic papers via Scholar API and sync to Supabase
# =============================================================================

from prefect import task, get_run_logger


@task(name="Run Scholar API")
def run_scholar_api():
    """Gather academic papers via Scholar API and sync to Supabase."""
    logger = get_run_logger()
    logger.info("🎓 Running Scholar API...")
    
    from src.gathering.scholar_api import main as scholar_main
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
