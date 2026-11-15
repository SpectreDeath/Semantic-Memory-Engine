"""
ScrapeGraphAI Harvester Extension

Purpose: Web scraping using ScrapeGraphAI's graph-based AI scraping
"""

try:
    from .plugin import ScrapeGraphHarvester, register_extension
except ImportError:
    from extensions.ext_scrapegraph_harvester.plugin import ScrapeGraphHarvester, register_extension

__all__ = ["ScrapeGraphHarvester", "register_extension"]
