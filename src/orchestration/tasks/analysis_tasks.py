# =============================================================================
# Analysis Tasks
# =============================================================================
# Generate agentic forensic summaries and run alerts
# =============================================================================

from prefect import task, get_run_logger


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
