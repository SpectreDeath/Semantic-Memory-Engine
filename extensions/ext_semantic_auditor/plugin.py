import os
import json
import logging
import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports

logger = logging.getLogger("LawnmowerMan.SemanticAuditor")

class SemanticAuditor:
    """
    Semantic Auditor v1.0
    Detects semantic drift in model outputs by comparing recent samples against master signatures.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id")
        self.signatures_path = r"d:\SME\data\signatures.json"

    async def on_startup(self):
        """
        Initialize the semantic auditor.
        """
        logger.info(f"[{self.plugin_id}] Semantic Auditor initialized.")

    def get_tools(self) -> list:
        return [self.audit_semantic_stability]

    async def audit_semantic_stability(self, model_family: str) -> str:
        """
        MCP Tool: audit_semantic_stability(model_family)
        
        Pulls the last 50 samples of the specified model from nexus_db,
        compares their semantic centroid against the "Master Signature" 
        in data/signatures.json, and returns a Drift Score.
        
        If score > 0.15, triggers a [LOGIC SHIFT DETECTED] warning.
        """
        try:
            # 1. Load master signature from signatures.json
            master_signature = self._load_master_signature(model_family)
            if not master_signature:
                return json.dumps({
                    "error": f"Master signature not found for model family: {model_family}",
                    "status": "failed"
                })

            # 2. Pull last 50 samples from nexus_db
            recent_samples = self._get_recent_samples(model_family, limit=50)
            if not recent_samples:
                return json.dumps({
                    "error": f"No recent samples found for model family: {model_family}",
                    "status": "failed"
                })

            # 3. Calculate semantic centroid of recent samples
            centroid = self._calculate_semantic_centroid(recent_samples)
            
            # 4. Compare centroid against master signature
            drift_score = self._calculate_drift_score(master_signature, centroid)
            
            # 5. Check for logic shift warning
            warning_triggered = drift_score > 0.15
            warning_message = "[LOGIC SHIFT DETECTED]" if warning_triggered else "No significant drift detected"
            
            # 6. Return results
            result = {
                "model_family": model_family,
                "sample_count": len(recent_samples),
                "drift_score": round(drift_score, 4),
                "warning_triggered": warning_triggered,
                "warning_message": warning_message,
                "master_signature": master_signature,
                "recent_centroid": centroid,
                "analysis": {
                    "master_vector_length": len(master_signature.get("vector", [])),
                    "centroid_vector_length": len(centroid),
                    "features_compared": len([f for f in master_signature.get("features", []) if f in centroid])
                }
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error in semantic stability audit: {e}")
            return json.dumps({
                "error": str(e),
                "status": "failed"
            })

    def _load_master_signature(self, model_family: str) -> Optional[Dict[str, Any]]:
        """Load the master signature for the specified model family."""
        try:
            if not os.path.exists(self.signatures_path):
                logger.error(f"Signatures file not found: {self.signatures_path}")
                return None
                
            with open(self.signatures_path, 'r') as f:
                signatures = json.load(f)
                
            if "families" not in signatures or model_family not in signatures["families"]:
                logger.error(f"Model family '{model_family}' not found in signatures")
                return None
                
            family_data = signatures["families"][model_family]
            return {
                "features": signatures.get("features", []),
                "vector": family_data.get("vector", []),
                "family": model_family
            }
            
        except Exception as e:
            logger.error(f"Failed to load master signature: {e}")
            return None

    def _get_recent_samples(self, model_family: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Pull recent samples from nexus_db for the specified model family.
        This assumes there's a table that stores model outputs with family information.
        """
        try:
            # Query the nexus database for recent samples
            # This query assumes there's a table that stores model outputs
            # We'll look for tables that might contain model data
            tables = self._get_available_tables()
            
            # Try to find a suitable table for model outputs
            model_table = self._find_model_table(tables)
            if not model_table:
                logger.warning("No suitable model output table found in nexus database")
                return []
            
            # Query for recent samples of the specified model family
            sql = f"""
                SELECT text_sample, metadata 
                FROM {model_table} 
                WHERE model_family = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            
            results = self.nexus.nexus.query(sql, (model_family, limit))
            
            samples = []
            for row in results:
                text_sample = row.get("text_sample", "")
                metadata = row.get("metadata", "{}")
                
                if text_sample:
                    samples.append({
                        "text": text_sample,
                        "metadata": json.loads(metadata) if isinstance(metadata, str) else metadata
                    })
            
            return samples
            
        except Exception as e:
            logger.error(f"Failed to get recent samples: {e}")
            return []

    def _get_available_tables(self) -> List[str]:
        """Get list of available tables in the nexus database."""
        try:
            sql = "SELECT name FROM sqlite_master WHERE type='table'"
            results = self.nexus.nexus.query(sql)
            return [row["name"] for row in results]
        except Exception as e:
            logger.error(f"Failed to get available tables: {e}")
            return []

    def _find_model_table(self, tables: List[str]) -> Optional[str]:
        """Find a table that likely contains model outputs."""
        # Look for tables that might contain model data
        priority_tables = ["forensic_events", "synthetic_baselines", "laboratory_events"]
        
        for table in priority_tables:
            if table in tables:
                return table
                
        # If no priority table found, look for any table with 'model' or 'output' in the name
        for table in tables:
            if any(keyword in table.lower() for keyword in ["model", "output", "sample", "text"]):
                return table
                
        # Fallback to the first available table
        return tables[0] if tables else None

    def _calculate_semantic_centroid(self, samples: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate the semantic centroid of recent samples.
        Uses the same feature extraction logic as the SDA engine.
        """
        if not samples:
            return {}
            
        # Get features from master signature for consistent vectorization
        master_signature = self._load_master_signature("GPT-Family")  # Use GPT as default for feature list
        if not master_signature:
            return {}
            
        features = master_signature.get("features", [])
        
        # Extract feature vectors from all samples
        feature_vectors = []
        for sample in samples:
            text = sample.get("text", "")
            if text:
                vector = self._extract_features(text, features)
                if vector:
                    feature_vectors.append(vector)
        
        if not feature_vectors:
            return {}
            
        # Calculate centroid (mean) of all vectors
        centroid = {}
        for feature_idx, feature in enumerate(features):
            values = [vec[feature_idx] for vec in feature_vectors if feature_idx < len(vec)]
            if values:
                centroid[feature] = sum(values) / len(values)
            else:
                centroid[feature] = 0.0
                
        return centroid

    def _extract_features(self, text: str, features: List[str]) -> List[float]:
        """
        Extract feature vector from text based on signature features.
        Returns relative frequency of each feature word.
        """
        if not features or not text:
            return []
            
        words = text.lower().split()
        total_words = len(words)
        
        if total_words == 0:
            return [0.0] * len(features)
            
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Calculate relative frequency for each feature
        feature_vector = []
        for feature in features:
            feature_count = word_counts.get(feature.lower(), 0)
            relative_freq = feature_count / total_words
            feature_vector.append(relative_freq)
            
        return feature_vector

    def _calculate_drift_score(self, master_signature: Dict[str, Any], centroid: Dict[str, float]) -> float:
        """
        Calculate drift score using cosine distance between master signature and centroid.
        """
        if not master_signature or not centroid:
            return 0.0
            
        master_vector = master_signature.get("vector", [])
        features = master_signature.get("features", [])
        
        if not master_vector or not features:
            return 0.0
            
        # Align vectors by features
        centroid_vector = []
        for feature in features:
            centroid_vector.append(centroid.get(feature, 0.0))
        
        # Calculate cosine distance
        return self._cosine_distance(master_vector, centroid_vector)

    def _cosine_distance(self, vector_a: List[float], vector_b: List[float]) -> float:
        """
        Calculate cosine distance between two vectors.
        Returns value between 0.0 (identical) and 2.0 (opposite).
        """
        if len(vector_a) != len(vector_b):
            raise ValueError("Vectors must have the same dimensionality")
            
        # Handle zero vectors
        norm_a = math.sqrt(sum(x * x for x in vector_a))
        norm_b = math.sqrt(sum(x * x for x in vector_b))
        
        if norm_a == 0 or norm_b == 0:
            return 1.0  # Maximum distance for zero vectors
            
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        
        # Calculate cosine similarity
        cosine_similarity = dot_product / (norm_a * norm_b)
        
        # Convert to distance (1 - similarity gives 0 to 2 range)
        cosine_distance = 1.0 - cosine_similarity
        
        return max(0.0, min(2.0, cosine_distance))


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return a SemanticAuditor instance."""
    return SemanticAuditor(manifest, nexus_api)


def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)