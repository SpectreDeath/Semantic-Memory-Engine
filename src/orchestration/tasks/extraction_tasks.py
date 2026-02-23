# =============================================================================
# Extraction Tasks
# =============================================================================
# Extract authors from research papers for OSINT pivoting
# =============================================================================

import json
from pathlib import Path
from prefect import task, get_run_logger


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
    return targets[:5]  # Limit for the operational run
