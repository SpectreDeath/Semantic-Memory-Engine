import requests
import logging
import time
from typing import List, Dict, Tuple, Optional
from waybackpy import WaybackMachineCDXServerAPI

logger = logging.getLogger("LawnmowerMan.ArchivalDiff.Scout")

class WaybackScout:
    """
    Handles discovery of archival snapshots via the Wayback Machine CDX API.
    Identifies divergent snapshots based on SHA-1 digests.
    """
    
    CDX_URL = "https://web.archive.org/cdx/search/cdx"
    
    def __init__(self, user_agent: str = "SME-Archival-Diff-Extension/1.0"):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}

    def get_snapshot_history(self, url: str) -> List[Dict[str, str]]:
        """
        Retrieves the snapshot history for a URL using the CDX API.
        Filters for 200 OK status codes by default.
        """
        params = {
            "url": url,
            "output": "json",
            "fl": "timestamp,original,mimetype,statuscode,digest",
            "filter": "statuscode:200",
            "collapse": "digest"  # Get unique versions
        }
        
        try:
            logger.info(f"Querying Wayback CDX for: {url}")
            response = requests.get(self.CDX_URL, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data or len(data) < 2:
                logger.warning(f"No snapshot history found for {url}")
                return []
            
            # First row is headers
            keys = data[0]
            snapshots = [dict(zip(keys, row)) for row in data[1:]]
            
            # Sort by timestamp ascending
            snapshots.sort(key=lambda x: x['timestamp'])
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to retrieve CDX history for {url}: {e}")
            return []

    def find_divergent_snapshots(self, url: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Finds the two most recent *different* snapshots based on SHA-1 digest.
        """
        snapshots = self.get_snapshot_history(url)
        if len(snapshots) < 2:
            return None, None
            
        # Since we use 'collapse:digest', most snapshots in the list should already be different.
        # But we'll verify just in case.
        
        # Take the most recent two
        latest = snapshots[-1]
        previous = snapshots[-2]
        
        if latest['digest'] != previous['digest']:
            return previous, latest
            
        # If they are same (unlikely with collapse), search backwards
        latest_digest = latest['digest']
        for i in range(len(snapshots) - 2, -1, -1):
            if snapshots[i]['digest'] != latest_digest:
                return snapshots[i], latest
                
        return None, latest

    def get_snapshot_content(self, wb_url: str) -> Optional[str]:
        """
        Fetch the raw HTML content of a snapshot.
        """
        try:
            # We want the raw content (id_ suffix in wayback)
            if "/web/" in wb_url and not wb_url.endswith("id_"):
                # Insert id_ after the timestamp
                parts = wb_url.split("/")
                # e.g. https://web.archive.org/web/20210101000000/http://example.com
                # -> https://web.archive.org/web/20210101000000id_/http://example.com
                for i, part in enumerate(parts):
                    if len(part) == 14 and part.isdigit():
                        parts[i] = part + "id_"
                        break
                wb_url = "/".join(parts)

            response = requests.get(wb_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Check for soft-404 signatures in body
            content = response.text
            if self._is_soft_404(content):
                logger.warning(f"Soft 404 detected for snapshot: {wb_url}")
                return None
                
            return content
        except Exception as e:
            logger.error(f"Failed to fetch snapshot content from {wb_url}: {e}")
            return None

    def _is_soft_404(self, content: str) -> bool:
        """
        Detects common 'Page Not Found' or 'Redirect' patterns in HTML.
        """
        soft_404_indicators = [
            "404 - File or directory not found",
            "Page not found",
            "The requested page could not be found",
            "This page has moved",
            "Access Denied",
            "window.location.replace",
            "http-equiv=\"refresh\""
        ]
        
        lower_content = content.lower()
        for indicator in soft_404_indicators:
            if indicator.lower() in lower_content:
                return True
        return False

    def build_wayback_url(self, timestamp: str, original_url: str) -> str:
        return f"https://web.archive.org/web/{timestamp}/{original_url}"
