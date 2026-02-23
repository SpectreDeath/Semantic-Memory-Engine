# =============================================================================
# RSS Tasks
# =============================================================================
# Gather news via RSS Bridge and sync to Supabase
# =============================================================================

from prefect import task, get_run_logger


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
