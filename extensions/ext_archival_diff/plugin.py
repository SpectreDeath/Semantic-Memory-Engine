import logging
import json
from typing import Dict, Any, List
from .scout import WaybackScout
from .analyst import ForensicAnalyst
from .exporter import SmeExporter

logger = logging.getLogger("LawnmowerMan.ArchivalDiff")

class ArchivalDiffExtension:
    """
    SME Extension: Detect Data Scrubbing via Wayback Machine Comparison.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus_api = nexus_api
        self.plugin_id = manifest.get("plugin_id", "ext_archival_diff")
        
        # Initialize modules
        self.scout = WaybackScout()
        self.analyst = ForensicAnalyst()
        self.exporter = SmeExporter()

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Archival Diff Extension activated.")

    def get_tools(self) -> List[Any]:
        return [self.scan_for_scrubbing]

    async def scan_for_scrubbing(self, target_url: str) -> str:
        """
        Scans a URL for semantic deletions compared to its previous Wayback snapshot.
        
        Args:
            target_url: The URL of the government page to check.
            
        Returns:
            JSON string containing the diff analysis result.
        """
        logger.info(f"Starting archival scrub scan for: {target_url}")
        
        try:
            # 1. Discover snapshots
            old_snap, new_snap = self.scout.find_divergent_snapshots(target_url)
            
            if not old_snap or not new_snap:
                return json.dumps({
                    "status": "inconclusive",
                    "reason": "Insufficient snapshot history or no divergent content found in archive index."
                })
            
            # 2. Fetch content
            old_url = self.scout.build_wayback_url(old_snap['timestamp'], target_url)
            new_url = self.scout.build_wayback_url(new_snap['timestamp'], target_url)
            
            old_html = self.scout.get_snapshot_content(old_url)
            new_html = self.scout.get_snapshot_content(new_url)
            
            if not old_html or not new_html:
                return json.dumps({
                    "status": "error",
                    "reason": "Failed to retrieve snapshot content from Wayback Machine."
                })
            
            # 3. Analyze diff
            diff_result = self.analyst.semantic_diff(old_html, new_html)
            
            # 4. Export to Postgres / SME
            metadata = {
                "url": target_url,
                "snapshot_old": {
                    "timestamp": old_snap['timestamp'],
                    "url": old_url,
                    "digest": old_snap['digest']
                },
                "snapshot_new": {
                    "timestamp": new_snap['timestamp'],
                    "url": new_url,
                    "digest": new_snap['digest']
                }
            }
            
            self.exporter.export_diff(diff_result, metadata)
            
            # 5. Return report
            report = {
                "status": "complete",
                "url": target_url,
                "scrubbing_detected": len(diff_result['deleted_content']) > 0,
                "added_count": diff_result['summary']['total_added'],
                "deleted_count": diff_result['summary']['total_deleted'],
                "evidence": diff_result['deleted_content'][:3], # Sample evidence
                "metadata": metadata
            }
            
            return json.dumps(report, indent=2)
            
        except Exception as e:
            logger.error(f"Error during scrub scan: {e}")
            return json.dumps({"status": "error", "error": str(e)})

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Optional: Automatically scan on a schedule or ingestion if URL is present.
        """
        pass

def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    return ArchivalDiffExtension(manifest, nexus_api)
