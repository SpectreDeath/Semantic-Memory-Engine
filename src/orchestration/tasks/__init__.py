# =============================================================================
# SME Pipeline Tasks
# =============================================================================
# Extracted from pipeline.py for better organization and testability
# =============================================================================

from .rss_tasks import run_rss_bridge
from .scholar_tasks import run_scholar_api
from .osint_tasks import run_osint_scan, stream_bipartite
from .extraction_tasks import extract_targets
from .analysis_tasks import run_forensic_summary

__all__ = [
    "run_rss_bridge",
    "run_scholar_api",
    "run_osint_scan",
    "stream_bipartite",
    "extract_targets",
    "run_forensic_summary",
]
