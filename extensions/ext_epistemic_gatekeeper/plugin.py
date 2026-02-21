import os
import json
import logging
from typing import Dict, Any, List, Set

# Import optimized types
from src.sme.epistemic_validator import DataNode

# Import shared trust logic
from gateway.gatekeeper_logic import calculate_trust_score, calculate_entropy, calculate_burstiness, calculate_vault_proximity, analyze_model_origin

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports
from src.core.plugin_base import BasePlugin
from src.utils.error_handling import ErrorHandler, create_error_response, OperationContext
from src.utils.performance import get_performance_monitor, cache_result, LRUCache

logger = logging.getLogger("LawnmowerMan.Gatekeeper")

class EpistemicGatekeeper(BasePlugin):
    """
    Epistemic Gatekeeper Extension (v1.2.0).
    Provides volume-based trust auditing (Heat Maps) and governance.
    """
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.error_handler = ErrorHandler(self.plugin_id)
        self.monitor = get_performance_monitor(self.plugin_id)
        self.file_cache = LRUCache(max_size=1000, ttl_seconds=600)  # Cache file contents for 10 minutes

    async def on_startup(self):
        """
        Initialize the Epistemic Gatekeeper.
        """
        try:
            logger.info(f"[{self.plugin_id}] Gatekeeper Online. Trust algorithms active.")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start Gatekeeper: {e}")

    async def on_shutdown(self):
        """
        Clean shutdown of the Epistemic Gatekeeper.
        """
        try:
            logger.info(f"[{self.plugin_id}] Gatekeeper shutdown complete")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error during shutdown: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Epistemic Gatekeeper does not process on_ingestion directly.
        It provides tools for trust auditing and semantic analysis.
        """
        return {
            "status": "skipped",
            "reason": "Epistemic Gatekeeper provides auditing tools, not direct ingestion processing"
        }

    def get_tools(self) -> list:
        return [
            self.audit_folder_veracity,
            self.semantic_nexus_check,
            self.get_gatekeeper_stats,
            self.clear_file_cache
        ]

    async def audit_folder_veracity(self, folder_path: str) -> str:
        """
        Recursively audits a folder, generating a Heat Map of Trust Scores (NTS).
        Returns a JSON report classifying files as Human, Synthetic, or Mixed.
        """
        if not os.path.exists(folder_path):
            return json.dumps({"error": f"Path not found: {folder_path}"})
            
        file_stats = []
        total_files = 0
        synthetic_count = 0
        human_count = 0
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.txt', '.md', '.log', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        if len(content) < 50:
                            continue
                            
                        # Calculate Metrics
                        entropy = calculate_entropy(content)
                        burstiness = calculate_burstiness(content)
                        proximity = calculate_vault_proximity(content)
                        trust_data = calculate_trust_score(entropy, burstiness, proximity)
                        
                        # SDA Profiler v1.3.0 Attribution
                        attribution = analyze_model_origin(content)
                        attr_msg = ""
                        if attribution["family"] != "Unknown":
                            attr_msg = f"High probability match: {attribution['family']} (Certainty: {attribution['confidence']}%)"

                        nts = trust_data["nts"]
                        verdict = trust_data["label"]
                        
                        # Updated Classifications for v1.2.0
                        if nts < 50:
                            synthetic_count += 1
                        elif nts > 80:
                            human_count += 1
                            
                        node = DataNode(
                            file=file,
                            path=file_path,
                            entropy=entropy,
                            burstiness=burstiness,
                            vault_proximity=proximity,
                            nts=nts,
                            verdict=verdict,
                            attribution=str(attribution),
                            sda_warning=attr_msg
                        )
                        file_stats.append(node)
                        total_files += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to audit {file}: {e}")

        # Calculate Percentages
        high_confidence_pct = (human_count / total_files * 100) if total_files > 0 else 0.0
        synthetic_risk_pct = (synthetic_count / total_files * 100) if total_files > 0 else 0.0
        uncertain_pct = 100.0 - (high_confidence_pct + synthetic_risk_pct)

        # Generate Veracity Report
        report = {
            "veracity_report": {
                "folder_path": folder_path,
                "total_scanned": total_files,
                "metrics": {
                    "high_confidence_percentage": round(high_confidence_pct, 1),
                    "synthetic_risk_percentage": round(synthetic_risk_pct, 1),
                    "uncertain_percentage": round(uncertain_pct, 1)
                },
                "counts": {
                    "human_grounded": human_count,
                    "synthetic_hazard": synthetic_count,
                    "uncertain": total_files - (human_count + synthetic_count)
                },
                "global_trust_ratio": round(human_count / total_files, 2) if total_files > 0 else 0
            },
            "detailed_map": [n.to_dict() for n in sorted(file_stats, key=lambda x: x.nts)]
        }
        
        return json.dumps(report, indent=2)

    async def semantic_nexus_check(self, new_entities: List[str], nexus_entities: Set[str]) -> float:
        """
        Calculates a trust signal based on how well new data aligns 
        with the established 'Nexus' memory.
        """
        logger.info("Executing Weighted Entity Overlap and Entropy Divergence Check")
        if not nexus_entities:
            return 1.0  # Default trust if Nexus is empty

        new_set = set(new_entities)
        intersection = new_set.intersection(nexus_entities)
        
        # Jaccard Similarity: Intersection over Union
        union = new_set.union(nexus_entities)
        similarity = len(intersection) / len(union) if union else 0
        
        # Divergence Penalty: If new data introduces too many 
        # unknown variables, we flag it.
        novelty_ratio = len(new_set - nexus_entities) / len(new_set) if new_set else 0
        
        # Final Trust Signal (0.0 to 1.0)
        # We want high similarity and low novelty for "High Trust"
        trust_signal = (similarity * 0.7) + ((1 - novelty_ratio) * 0.3)
        
        return round(trust_signal, 4)

    async def get_gatekeeper_stats(self) -> str:
        """Get statistics about the Gatekeeper's performance and cache usage."""
        try:
            cache_stats = self.file_cache.get_stats()
            performance_stats = self.monitor.get_all_stats()
            
            stats = {
                "plugin_id": self.plugin_id,
                "cache_stats": cache_stats,
                "performance_stats": performance_stats,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(stats, indent=2)
        except Exception as e:
            return self.error_handler.handle_tool_error(e, "get_gatekeeper_stats")

    async def clear_file_cache(self) -> str:
        """Clear the file content cache."""
        try:
            self.file_cache.clear()
            return json.dumps({
                "status": "success",
                "message": "File cache cleared successfully"
            }, indent=2)
        except Exception as e:
            return self.error_handler.handle_tool_error(e, "clear_file_cache")


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return an EpistemicGatekeeper instance."""
    return EpistemicGatekeeper(manifest, nexus_api)


def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)
