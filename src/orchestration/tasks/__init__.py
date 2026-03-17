# =============================================================================
# SME Pipeline Tasks
# =============================================================================
# Extracted from pipeline.py for better organization and testability
# =============================================================================

from .analysis_tasks import run_forensic_summary
from .extraction_tasks import extract_targets
from .osint_tasks import run_osint_scan, stream_bipartite
from .rss_tasks import run_rss_bridge
from .scholar_tasks import run_scholar_api

__all__ = [
    "extract_targets",
    "run_forensic_summary",
    "run_osint_scan",
    "run_rss_bridge",
    "run_scholar_api",
    "stream_bipartite",
]
