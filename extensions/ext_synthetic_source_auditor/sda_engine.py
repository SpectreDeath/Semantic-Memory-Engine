import math
import re
import json
import os
from collections import Counter
from typing import Dict, Any, List, Tuple, Optional

class SourceDeAnonymizationEngine:
    """
    Source De-Anonymization (SDA) Engine
    Uses Cosine Similarity to match text against signatures in data/signatures.json
    """
    
    def __init__(self, signatures_path: str = r"d:\SME\data\signatures.json"):
        self.signatures_path = signatures_path
        self.signatures = self._load_signatures()
        
    def _load_signatures(self) -> Dict[str, Any]:
        """Load model signatures from JSON file."""
        if not os.path.exists(self.signatures_path):
            raise FileNotFoundError(f"Signatures file not found: {self.signatures_path}")
            
        try:
            with open(self.signatures_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load signatures: {e}")
    
    def _extract_features(self, text: str) -> List[float]:
        """
        Extract feature vector from text based on signature features.
        Returns relative frequency of each feature word.
        """
        if not self.signatures or "features" not in self.signatures:
            return []
            
        features = self.signatures["features"]
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return [0.0] * len(features)
            
        word_counts = Counter(words)
        
        # Calculate relative frequency for each feature
        feature_vector = []
        for feature in features:
            feature_count = word_counts.get(feature, 0)
            relative_freq = feature_count / total_words
            feature_vector.append(relative_freq)
            
        return feature_vector
    
    def _cosine_similarity(self, vector_a: List[float], vector_b: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        Returns value between 0.0 (no similarity) and 1.0 (identical).
        """
        if len(vector_a) != len(vector_b):
            raise ValueError("Vectors must have the same dimensionality")
            
        # Handle zero vectors
        norm_a = math.sqrt(sum(x * x for x in vector_a))
        norm_b = math.sqrt(sum(x * x for x in vector_b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        
        # Calculate cosine similarity
        similarity = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text and return model attribution with confidence scores.
        """
        if not text or not text.strip():
            return {
                "detected_family": "Unknown",
                "confidence": 0.0,
                "similarity_scores": {},
                "analysis": {
                    "feature_count": 0,
                    "total_words": 0,
                    "feature_vector": []
                }
            }
        
        # Extract feature vector from input text
        feature_vector = self._extract_features(text)
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if not self.signatures or "families" not in self.signatures:
            return {
                "detected_family": "Unknown",
                "confidence": 0.0,
                "similarity_scores": {},
                "analysis": {
                    "feature_count": len(feature_vector),
                    "total_words": total_words,
                    "feature_vector": feature_vector
                }
            }
        
        # Calculate similarity against each family
        similarity_scores = {}
        max_similarity = 0.0
        best_family = "Unknown"
        
        for family_name, family_data in self.signatures["families"].items():
            family_vector = family_data.get("vector", [])
            
            if len(family_vector) != len(feature_vector):
                # Skip families with incompatible vector dimensions
                continue
                
            similarity = self._cosine_similarity(feature_vector, family_vector)
            similarity_scores[family_name] = round(similarity, 4)
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_family = family_name
        
        # Convert similarity to percentage confidence
        confidence = round(max_similarity * 100, 1)
        
        # Apply attribution threshold (80% confidence required for attribution)
        if confidence < 80.0:
            detected_family = "Unknown"
        else:
            detected_family = best_family
            
        return {
            "detected_family": detected_family,
            "confidence": confidence,
            "similarity_scores": similarity_scores,
            "analysis": {
                "feature_count": len(feature_vector),
                "total_words": total_words,
                "feature_vector": feature_vector,
                "best_match": best_family,
                "raw_similarity": max_similarity
            }
        }
    
    def get_signature_info(self) -> Dict[str, Any]:
        """Get information about loaded signatures."""
        if not self.signatures:
            return {"status": "No signatures loaded"}
            
        return {
            "features": self.signatures.get("features", []),
            "families": list(self.signatures.get("families", {}).keys()),
            "total_features": len(self.signatures.get("features", [])),
            "total_families": len(self.signatures.get("families", {}))
        }
    
    def add_signature_family(self, family_name: str, feature_vector: List[float]) -> bool:
        """
        Add a new signature family to the signatures database.
        Returns True if successful, False otherwise.
        """
        try:
            # Validate vector length
            if "features" not in self.signatures:
                self.signatures["features"] = []
                
            expected_length = len(self.signatures["features"])
            if len(feature_vector) != expected_length:
                raise ValueError(f"Vector length {len(feature_vector)} doesn't match expected length {expected_length}")
            
            # Add or update family
            if "families" not in self.signatures:
                self.signatures["families"] = {}
                
            self.signatures["families"][family_name] = {"vector": feature_vector}
            
            # Save to file
            with open(self.signatures_path, 'w') as f:
                json.dump(self.signatures, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Failed to add signature family: {e}")
            return False
    
    def compare_texts(self, text_a: str, text_b: str) -> Dict[str, Any]:
        """
        Compare two texts and return their similarity score.
        """
        vector_a = self._extract_features(text_a)
        vector_b = self._extract_features(text_b)
        
        if len(vector_a) != len(vector_b):
            return {"error": "Texts have incompatible feature vectors"}
            
        similarity = self._cosine_similarity(vector_a, vector_b)
        
        return {
            "similarity_score": round(similarity, 4),
            "similarity_percentage": round(similarity * 100, 1),
            "analysis": {
                "text_a_features": len(vector_a),
                "text_b_features": len(vector_b),
                "text_a_words": len(re.findall(r'\b\w+\b', text_a.lower())),
                "text_b_words": len(re.findall(r'\b\w+\b', text_b.lower()))
            }
        }

def create_sda_engine(signatures_path: str = r"d:\SME\data\signatures.json") -> SourceDeAnonymizationEngine:
    """Factory function to create and return an SDA engine instance."""
    return SourceDeAnonymizationEngine(signatures_path)