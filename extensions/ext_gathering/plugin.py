import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Gathering")

try:
    from src.gathering.web_researcher import WebResearcher
except ImportError:
    WebResearcher = None

try:
    from src.gathering.osint_toolkit import OSINTToolkit
except ImportError:
    OSINTToolkit = None

try:
    from src.gathering.rss_bridge import RSSBridge
except ImportError:
    RSSBridge = None

try:
    from src.gathering.scholar_api import ScholarAPI
except ImportError:
    ScholarAPI = None

try:
    from src.gathering.cloud_fetcher import CloudFetcher
except ImportError:
    CloudFetcher = None


class GatheringExtension(BasePlugin):
    """
    Data Gathering Extension for SME.
    Provides web researcher, OSINT toolkit, RSS bridge, scholar API, and cloud fetching.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.web_researcher = WebResearcher() if WebResearcher else None
        self.osint = OSINTToolkit() if OSINTToolkit else None
        self.rss = RSSBridge() if RSSBridge else None
        self.scholar = ScholarAPI() if ScholarAPI else None
        self.cloud = CloudFetcher() if CloudFetcher else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Data Gathering extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.research_web,
            self.osint_scan,
            self.fetch_rss,
            self.fetch_scholar,
            self.fetch_cloud,
        ]

    async def research_web(self, query: str, num_results: int = 10) -> str:
        """Perform comprehensive web research."""
        if not self.web_researcher:
            return json.dumps({"error": "WebResearcher not available"})
        try:
            results = self.web_researcher.research(query, num_results)
            return json.dumps({"query": query, "num_results": num_results, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def osint_scan(self, target: str, scan_types: list[str] = None) -> str:
        """Perform OSINT scan on target."""
        if not self.osint:
            return json.dumps({"error": "OSINTToolkit not available"})
        try:
            if scan_types is None:
                scan_types = ["whois", "dns", "social"]
            results = self.osint.scan(target, scan_types)
            return json.dumps({"target": target, "scan_types": scan_types, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def fetch_rss(self, feed_url: str, limit: int = 20) -> str:
        """Fetch and parse RSS/Atom feed."""
        if not self.rss:
            return json.dumps({"error": "RSSBridge not available"})
        try:
            items = self.rss.fetch(feed_url, limit)
            return json.dumps({"feed_url": feed_url, "limit": limit, "items": items})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def fetch_scholar(self, query: str, num_papers: int = 10) -> str:
        """Fetch academic papers from scholarly APIs."""
        if not self.scholar:
            return json.dumps({"error": "ScholarAPI not available"})
        try:
            papers = self.scholar.fetch(query, num_papers)
            return json.dumps({"query": query, "num_papers": num_papers, "papers": papers})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def fetch_cloud(self, source: str, path: str, options: dict = None) -> str:
        """Fetch data from cloud storage."""
        if not self.cloud:
            return json.dumps({"error": "CloudFetcher not available"})
        try:
            data = self.cloud.fetch(source, path, options)
            return json.dumps({"source": source, "path": path, "data": data})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return GatheringExtension(manifest, nexus_api)
