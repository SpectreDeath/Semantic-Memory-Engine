import os
import json
import logging
import math
import hashlib
import statistics
import re
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List

# NexusAPI: use self.nexus.get_hsm() — no gateway imports
# Import shared logic
from gateway.gatekeeper_logic import calculate_trust_score, calculate_entropy, calculate_burstiness
# Import SDA engine
try:
    from .sda_engine import SourceDeAnonymizationEngine
except ImportError:
    import sys
    from pathlib import Path
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from sda_engine import SourceDeAnonymizationEngine

logger = logging.getLogger("LawnmowerMan.SSA")

class AnalyticAuditor:
    """
    Synthetic Source Auditor (SSA) v1.0.
    Detects low-entropy synthetic text and vaults it for counter-intelligence.
    Now includes Source De-Anonymization (SDA) capabilities.
    """
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id")
        # Initialize SDA engine
        self.sda_engine = SourceDeAnonymizationEngine()

    async def on_startup(self):
        """
        Initialize the 'nexus_synthetic_baselines' table in the core DB.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS nexus_synthetic_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                text_sample TEXT NOT NULL,
                entropy_score REAL NOT NULL,
                timestamp TEXT,
                integrity_hash TEXT
            )
        """
        try:
            # We access the underlying sqlite connection via nexus_api.nexus.conn 
            # or execute directly if exposed. SmeCoreBridge exposes .nexus (NexusDB).
            # NexusDB has execute(sql, params).
            self.nexus.nexus.execute(sql)
            logger.info(f"[{self.plugin_id}] 'nexus_synthetic_baselines' table initialized.")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to init DB table: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Automatically audits ingestion stream for synthetic patterns.
        Now includes SDA analysis for model attribution.
        """
        if not raw_data or len(raw_data) < 50:
            return {"status": "skipped", "reason": "too_short"}

        # Calculate Entropy & Burstiness via Shared Logic
        entropy = calculate_entropy(raw_data)
        burstiness = calculate_burstiness(raw_data)
        
        # SDA Analysis for model attribution
        sda_result = self.sda_engine.analyze_text(raw_data)
        
        # Threshold Check for Vaulting
        # Vault if clearly synthetic (Low Entropy OR Low Burstiness)
        if entropy < 4.0 or (burstiness < 2.0 and len(raw_data) > 100):
            logger.warning(f"[{self.plugin_id}] SYNTHETIC SIGNAL (E:{entropy:.2f}, B:{burstiness:.2f}). Vaulting...")
            await self.vault_synthetic_pattern(raw_data, entropy, "DETECTED_SYNTHETIC")
            return {
                "alert": "SYNTHETIC_DETECTED",
                "entropy": entropy,
                "burstiness": burstiness,
                "sda_analysis": sda_result,
                "action": "vaulted"
            }
        
        return {
            "status": "cleared", 
            "entropy": entropy, 
            "burstiness": burstiness,
            "sda_analysis": sda_result
        }

    def get_tools(self) -> list:
        return [
            self.audit_text_integrity, 
            self.vault_synthetic_pattern, 
            self.compare_to_synthetic_baseline, 
            self.calculate_burstiness_metric,
            self.sda_analyze_model_origin,
            self.sda_get_signature_info,
            self.sda_compare_texts
        ]

    async def calculate_burstiness_metric(self, text: str) -> str:
        """
        Calculates the Standard Deviation of sentence lengths (Burstiness).
        """
        burstiness = calculate_burstiness(text)
        return json.dumps({
            "burstiness_score": round(burstiness, 4),
            "interpretation": "High Variance (Human)" if burstiness > 5.0 else "Low Variance (Synthetic)"
        })

    async def audit_text_integrity(self, text: str) -> str:
        """
        Calculates Shannon Entropy and Burstiness to measure text naturalness.
        """
        entropy = calculate_entropy(text)
        burstiness = calculate_burstiness(text)
        
        # Import Gatekeeper Logic (Dynamic to avoid circular imports during startup if logic not ready)
        try:
            from gateway.gatekeeper_logic import calculate_trust_score, calculate_vault_proximity
            proximity = calculate_vault_proximity(text)
            trust_data = calculate_trust_score(entropy, burstiness, proximity)
            verdict = trust_data["label"]
            nts = trust_data["nts"]
        except ImportError:
            # Fallback if logic library missing
            verdict = "Likely Human" if entropy >= 4.0 else "Likely Synthetic"
            nts = "N/A"
        
        return json.dumps({
            "entropy_bits": round(entropy, 4),
            "burstiness": round(burstiness, 4),
            "trust_score": nts,
            "verdict": verdict,
            "thresholds": {"entropy": 4.0, "trust": 50}
        }, indent=2)

    async def vault_synthetic_pattern(self, text: str, score: float, source_id: str = "MANUAL_SUBMISSION") -> str:
        """
        Vaults a confirmed synthetic text sample into the Nexus baseline.
        """
        timestamp = datetime.now().isoformat()
        # Create integrity hash
        data_hash = hashlib.sha256(text.encode()).hexdigest()
        
        sql = """
            INSERT INTO nexus_synthetic_baselines (source_id, text_sample, entropy_score, timestamp, integrity_hash)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.nexus.nexus.execute(sql, (source_id, text[:5000], score, timestamp, data_hash)) # Limit text size
            return json.dumps({"status": "vaulted", "id": data_hash, "score": score})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def compare_to_synthetic_baseline(self, text: str) -> str:
        """
        Compares new text against the 'Synthetic Baseline Vault' to find stylistic matches.
        """
        entropy = calculate_entropy(text)
        
        # Find samples with similar entropy (+/- 0.1)
        sql = """
            SELECT source_id, entropy_score, text_sample FROM nexus_synthetic_baselines
            WHERE entropy_score BETWEEN ? AND ?
            LIMIT 5
        """
        try:
            lower = entropy - 0.1
            upper = entropy + 0.1
            res = self.nexus.nexus.query(sql, (lower, upper))
            
            matches = []
            if res:
                for row in res:
                    matches.append({
                        "source": row["source_id"],
                        "baseline_entropy": row["entropy_score"],
                        "delta": abs(entropy - row["entropy_score"])
                    })
            
            return json.dumps({
                "input_entropy": entropy,
                "matches_found": len(matches),
                "closest_matches": sorted(matches, key=lambda x: x['delta'])
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def sda_analyze_model_origin(self, text: str) -> str:
        """
        Source De-Anonymization: Analyze text and return model attribution with confidence scores.
        """
        try:
            result = self.sda_engine.analyze_text(text)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": f"SDA Analysis failed: {str(e)}"})

    async def sda_get_signature_info(self) -> str:
        """
        Get information about loaded signatures.
        """
        try:
            info = self.sda_engine.get_signature_info()
            return json.dumps(info, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get signature info: {str(e)}"})

    async def sda_compare_texts(self, text_a: str, text_b: str) -> str:
        """
        Compare two texts and return their similarity score.
        """
        try:
            result = self.sda_engine.compare_texts(text_a, text_b)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Text comparison failed: {str(e)}"})


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return an AnalyticAuditor instance."""
    return AnalyticAuditor(manifest, nexus_api)


def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)
