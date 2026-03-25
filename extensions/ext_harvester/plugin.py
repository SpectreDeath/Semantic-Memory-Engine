import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Harvester")

try:
    from src.harvester.spider import Spider
except ImportError:
    Spider = None

try:
    from src.harvester.crawler import Crawler
except ImportError:
    Crawler = None

try:
    from src.harvester.forensic_scout import ForensicScout
except ImportError:
    ForensicScout = None

try:
    from src.harvester.search import SearchEngine
except ImportError:
    SearchEngine = None

try:
    from src.harvester.converter import SchemaConverter
except ImportError:
    SchemaConverter = None


class HarvesterExtension(BasePlugin):
    """
    Web Harvester Extension for SME.
    Provides web harvesting and ingestion tools including spider, crawler, forensic scout, search, and schema conversion.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.spider = Spider() if Spider else None
        self.crawler = Crawler() if Crawler else None
        self.scout = ForensicScout() if ForensicScout else None
        self.search = SearchEngine() if SearchEngine else None
        self.converter = SchemaConverter() if SchemaConverter else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Web Harvester extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.crawl_url,
            self.spider_scrape,
            self.forensic_search,
            self.web_search,
            self.convert_schema,
        ]

    async def crawl_url(self, url: str, depth: int = 2, pattern: str = None) -> str:
        """Crawl URL to specified depth."""
        if not self.crawler:
            return json.dumps({"error": "Crawler not available"})
        try:
            results = self.crawler.crawl(url, depth, pattern)
            return json.dumps({"url": url, "depth": depth, "pages_crawled": len(results)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def spider_scrape(self, url: str, selectors: list[str] = None) -> str:
        """Scrape URL using spider with CSS/XPath selectors."""
        if not self.spider:
            return json.dumps({"error": "Spider not available"})
        try:
            data = self.spider.scrape(url, selectors)
            return json.dumps({"url": url, "data": data})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def forensic_search(self, target: str, scan_type: str = "full") -> str:
        """Perform forensic search on target."""
        if not self.scout:
            return json.dumps({"error": "ForensicScout not available"})
        try:
            results = self.scout.search(target, scan_type)
            return json.dumps({"target": target, "scan_type": scan_type, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def web_search(self, query: str, num_results: int = 10, engine: str = "default") -> str:
        """Perform web search."""
        if not self.search:
            return json.dumps({"error": "SearchEngine not available"})
        try:
            results = self.search.search(query, num_results, engine)
            return json.dumps({"query": query, "num_results": num_results, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def convert_schema(self, data: Any, from_format: str, to_format: str) -> str:
        """Convert data between schemas/formats."""
        if not self.converter:
            return json.dumps({"error": "SchemaConverter not available"})
        try:
            converted = self.converter.convert(data, from_format, to_format)
            return json.dumps({"from": from_format, "to": to_format, "data": converted})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return HarvesterExtension(manifest, nexus_api)
