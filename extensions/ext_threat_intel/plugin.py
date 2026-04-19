import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.ThreatIntel")

THREAT_CACHE_FILE = Path(__file__).parent / "threat_cache.json"


class ThreatIntelProvider:
    def __init__(self):
        self.cache: dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self):
        if THREAT_CACHE_FILE.exists():
            try:
                with open(THREAT_CACHE_FILE) as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached threat lookups")
            except Exception as e:
                logger.exception(f"Failed to load threat cache: {e}")

    def _save_cache(self):
        with open(THREAT_CACHE_FILE, "w") as f:
            json.dump(self.cache, f, indent=2)

    def _is_valid_ip(self, value: str) -> bool:
        pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        return bool(re.match(pattern, value))

    def _is_valid_hash(self, value: str) -> bool:
        patterns = {
            "md5": r"^[a-fA-F0-9]{32}$",
            "sha1": r"^[a-fA-F0-9]{40}$",
            "sha256": r"^[a-fA-F0-9]{64}$",
        }
        return any(re.match(p, value) for p in patterns.values())

    def _is_valid_domain(self, value: str) -> bool:
        pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        return bool(re.match(pattern, value))

    def get_ioc_type(self, value: str) -> str | None:
        """Determine the type of IOC (Indicator of Compromise)."""
        value = value.strip()
        if self._is_valid_ip(value):
            return "ip"
        if self._is_valid_hash(value):
            return "hash"
        if self._is_valid_domain(value):
            return "domain"
        if value.startswith("http://") or value.startswith("https://"):
            return "url"
        return None

    def lookup_ip(self, ip: str, api_key: str | None = None) -> dict:
        """Look up IP reputation (mock for demo)."""
        if ip in self.cache:
            return self.cache[ip]

        result = {
            "indicator": ip,
            "type": "ip",
            "reputation": "unknown",
            "score": 0,
            "categories": [],
            "last_checked": datetime.now().isoformat(),
            "details": "Demo mode - configure API keys for real lookups",
        }

        self.cache[ip] = result
        self._save_cache()
        return result

    def lookup_hash(self, hash_value: str, api_key: str | None = None) -> dict:
        """Look up file hash reputation (mock for demo)."""
        if hash_value in self.cache:
            return self.cache[hash_value]

        result = {
            "indicator": hash_value,
            "type": "hash",
            "reputation": "unknown",
            "score": 0,
            "categories": [],
            "last_checked": datetime.now().isoformat(),
            "details": "Demo mode - configure API keys for real lookups",
        }

        self.cache[hash_value] = result
        self._save_cache()
        return result

    def lookup_domain(self, domain: str, api_key: str | None = None) -> dict:
        """Look up domain reputation (mock for demo)."""
        if domain in self.cache:
            return self.cache[domain]

        result = {
            "indicator": domain,
            "type": "domain",
            "reputation": "unknown",
            "score": 0,
            "categories": [],
            "last_checked": datetime.now().isoformat(),
            "details": "Demo mode - configure API keys for real lookups",
        }

        self.cache[domain] = result
        self._save_cache()
        return result

    def lookup_url(self, url: str, api_key: str | None = None) -> dict:
        """Look up URL reputation (mock for demo)."""
        if url in self.cache:
            return self.cache[url]

        result = {
            "indicator": url,
            "type": "url",
            "reputation": "unknown",
            "score": 0,
            "categories": [],
            "last_checked": datetime.now().isoformat(),
            "details": "Demo mode - configure API keys for real lookups",
        }

        self.cache[url] = result
        self._save_cache()
        return result

    def batch_lookup(self, indicators: list[str], api_key: str | None = None) -> list[dict]:
        """Batch lookup multiple indicators."""
        results = []
        for indicator in indicators:
            ioc_type = self.get_ioc_type(indicator)
            if ioc_type == "ip":
                results.append(self.lookup_ip(indicator, api_key))
            elif ioc_type == "hash":
                results.append(self.lookup_hash(indicator, api_key))
            elif ioc_type == "domain":
                results.append(self.lookup_domain(indicator, api_key))
            elif ioc_type == "url":
                results.append(self.lookup_url(indicator, api_key))
            else:
                results.append(
                    {
                        "indicator": indicator,
                        "type": "unknown",
                        "error": "Unable to determine IOC type",
                    }
                )
        return results

    def get_cached_results(self) -> list[dict]:
        return list(self.cache.values())

    def clear_cache(self):
        self.cache = {}
        self._save_cache()


class ThreatIntelExtension(BasePlugin):
    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.provider = ThreatIntelProvider()

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Threat Intelligence extension activated")

    def get_tools(self):
        return [
            self.lookup_indicator,
            self.lookup_ip,
            self.lookup_hash,
            self.lookup_domain,
            self.lookup_url,
            self.batch_lookup,
            self.get_cached_results,
            self.clear_threat_cache,
        ]

    async def lookup_indicator(self, indicator: str) -> str:
        """Auto-detect and look up any indicator."""
        ioc_type = self.provider.get_ioc_type(indicator)
        if not ioc_type:
            return json.dumps({"error": "Unable to determine indicator type"})

        if ioc_type == "ip":
            result = self.provider.lookup_ip(indicator)
        elif ioc_type == "hash":
            result = self.provider.lookup_hash(indicator)
        elif ioc_type == "domain":
            result = self.provider.lookup_domain(indicator)
        elif ioc_type == "url":
            result = self.provider.lookup_url(indicator)
        else:
            return json.dumps({"error": f"Unknown type: {ioc_type}"})

        return json.dumps(result)

    async def lookup_ip(self, ip: str) -> str:
        """Look up IP reputation."""
        return json.dumps(self.provider.lookup_ip(ip))

    async def lookup_hash(self, hash_value: str) -> str:
        """Look up file hash reputation."""
        return json.dumps(self.provider.lookup_hash(hash_value))

    async def lookup_domain(self, domain: str) -> str:
        """Look up domain reputation."""
        return json.dumps(self.provider.lookup_domain(domain))

    async def lookup_url(self, url: str) -> str:
        """Look up URL reputation."""
        return json.dumps(self.provider.lookup_url(url))

    async def batch_lookup(self, indicators: str) -> str:
        """Batch lookup multiple indicators (JSON array)."""
        try:
            indicator_list = json.loads(indicators) if indicators else []
        except json.JSONDecodeError:
            indicator_list = [i.strip() for i in indicators.split(",")]

        results = self.provider.batch_lookup(indicator_list)
        return json.dumps({"results": results})

    async def get_cached_results(self) -> str:
        """Get all cached threat lookups."""
        return json.dumps({"cache": self.provider.get_cached_results()})

    async def clear_threat_cache(self) -> str:
        """Clear the threat lookup cache."""
        self.provider.clear_cache()
        return json.dumps({"status": "cache_cleared"})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return ThreatIntelExtension(manifest, nexus_api)
