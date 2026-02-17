import httpx
import logging
import asyncio
from typing import List, Dict
from datetime import datetime

# Configure logging
logger = logging.getLogger("SME.WaybackScout")

class WaybackScout:
    """
    WaybackScout (v1.0.0): Archival Forensics Module.
    Leverages the Wayback Machine CDX API to track URI evolution and detect scrubbed content.
    """
    def __init__(self):
        self.api_url = "https://web.archive.org/cdx/search/cdx"
        self.base_vault = "https://web.archive.org/web/"
        self.headers = {"User-Agent": "SME-Forensic-Lab-Bot/1.0"}

    async def get_snapshot_history(self, url: str) -> List[Dict]:
        """
        Fetches a full index of snapshots, filtering out 404s and redirects.
        Uses digest-based collapsing to optimize for unique captures.
        """
        params = {
            "url": url,
            "output": "json",
            "fl": "timestamp,original,mimetype,statuscode,digest",
            "filter": "statuscode:200", # Forensic focus: only successful pages
            "collapse": "digest"        # ignore identical consecutive captures
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"Querying Wayback CDX for: {url}")
                response = await client.get(self.api_url, params=params, headers=self.headers)
                
                if response.status_code != 200:
                    logger.error(f"Wayback CDX API error: {response.status_code}")
                    return []
                    
                data = response.json()
                
                if len(data) <= 1: 
                    logger.info(f"No unique snapshot history found for {url}")
                    return []
                
                # Transform CDX rows into digestible dictionaries
                headers = data[0]
                snapshots = [dict(zip(headers, row)) for row in data[1:]]
                
                # Add human-readable datetime
                for snap in snapshots:
                    ts = snap['timestamp']
                    try:
                        dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
                        snap['human_date'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        snap['archive_url'] = f"{self.base_vault}{ts}/{snap['original']}"
                    except:
                        snap['human_date'] = ts

                logger.info(f"Found {len(snapshots)} unique archival snapshots")
                return snapshots
            except Exception as e:
                logger.error(f"WaybackScout API Failure: {e}")
                return []

    def identify_divergent_points(self, snapshots: List[Dict]) -> List[Dict]:
        """
        Identifies pairs of snapshots where the SHA-1 digest changed.
        This provides a roadmap for semantic drift analysis.
        """
        divergences = []
        for i in range(1, len(snapshots)):
            if snapshots[i]['digest'] != snapshots[i-1]['digest']:
                divergences.append({
                    "pre_change": snapshots[i-1],
                    "post_change": snapshots[i],
                    "divergence_type": "Digest Mismatch (Content Mutation)"
                })
        
        logger.info(f"Detected {len(divergences)} points of archival divergence")
        return divergences

    async def fetch_snapshot_content(self, archive_url: str) -> str:
        """ Fetches the raw text content of an archived snapshot. """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(archive_url, headers=self.headers, follow_redirects=True)
                if response.status_code == 200:
                    return response.text
                return ""
            except Exception as e:
                logger.error(f"Failed to fetch content from {archive_url}: {e}")
                return ""

async def main_demo():
    scout = WaybackScout()
    history = await scout.get_snapshot_history("google.com")
    divergences = scout.identify_divergent_points(history)
    for d in divergences:
        print(f"Divergence detected at {d['post_change']['human_date']}")

if __name__ == "__main__":
    asyncio.run(main_demo())
