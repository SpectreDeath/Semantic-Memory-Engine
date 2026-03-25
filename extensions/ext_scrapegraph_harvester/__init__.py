"""
ScrapeGraphAI Harvester Extension

Purpose: Web scraping using ScrapeGraphAI's graph-based AI scraping
"""

from .plugin import ScrapeGraphHarvester, register_extension

__all__ = ["ScrapeGraphHarvester", "register_extension"]
