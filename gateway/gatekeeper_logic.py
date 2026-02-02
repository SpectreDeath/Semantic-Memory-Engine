import math
import statistics
import re
import os
import glob
from collections import Counter
from typing import Dict, Any, List

VAULT_PATH = r"d:\SME\data\grok_vault"
_VAULT_CACHE = None

def _get_ngrams(text: str, n: int = 3) -> set:
    """Generate n-grams from text."""
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < n:
        return set()
    return set(zip(*[words[i:] for i in range(n)]))

def load_vault() -> List[set]:
    """Load vault signatures (cached). Returns list of n-gram sets."""
    global _VAULT_CACHE
    if _VAULT_CACHE is not None:
        return _VAULT_CACHE
    
    _VAULT_CACHE = []
    if not os.path.exists(VAULT_PATH):
        return _VAULT_CACHE

    for file_path in glob.glob(os.path.join(VAULT_PATH, "*.txt")):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if content:
                    _VAULT_CACHE.append(_get_ngrams(content))
        except Exception:
            pass
    return _VAULT_CACHE

class TrustScorer:
    """
    Epistemic Gatekeeper Trust Scoring Engine.
    Calculates Normalized Trust Score (NTS) based on Entropy, Burstiness, and Vault Proximity.
    """
    
    @staticmethod
    def calculate_entropy(data: str) -> float:
        """Compute Shannon Entropy in bits per symbol."""
        if not data:
            return 0.0
        counter = Counter(data)
        length = len(data)
        entropy = 0.0
        for count in counter.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def calculate_burstiness(text: str) -> float:
        """Calculate Burstiness: Standard Deviation of sentence lengths (in words)."""
        if not text:
            return 0.0
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) < 2:
            return 0.0
        # Count words per sentence
        lengths = [len(s.split()) for s in sentences]
        if len(lengths) < 2:
            return 0.0
        try:
            return statistics.stdev(lengths)
        except Exception:
            return 0.0

    @staticmethod
    def calculate_vault_proximity(text: str) -> float:
        """
        Calculate proximity to Grok Vault entries using Containment Score on trigrams.
        Returns a score between 0.0 (no match) and 1.0 (identical).
        """
        if not text:
            return 0.0
        
        vault_sigs = load_vault()
        if not vault_sigs:
            return 0.0
            
        text_grams = _get_ngrams(text)
        if not text_grams:
            return 0.0
            
        max_similarity = 0.0
        for vault_grams in vault_sigs:
            if not vault_grams:
                continue
            intersection = len(text_grams & vault_grams)
            # Use Containment score (how much of the text is present in the vault?)
            denominator = len(text_grams)
            
            if denominator > 0:
                sim = intersection / denominator
                if sim > max_similarity:
                    max_similarity = sim
                    
        return max_similarity

    @classmethod
    def calculate_trust_score(cls, entropy: float, burstiness: float, vault_proximity: float = 0.0) -> Dict[str, Any]:
        """
        Calculates the Normalized Trust Score (NTS).
        """
        # 1. Entropy Deficit (Base 4.5)
        entropy_deficit = max(0.0, 4.5 - entropy)
        entropy_penalty = entropy_deficit * 25.0
        
        # 2. Burstiness Penalty (Std Dev < 6.0)
        burstiness_deficit = max(0.0, 6.0 - burstiness)
        burstiness_penalty = burstiness_deficit * 8.0 
        
        # 3. Vault Proximity
        vault_penalty = vault_proximity * 60.0
        
        # Aggregation
        nts = 100.0 - (entropy_penalty + burstiness_penalty + vault_penalty)
        nts = max(0.0, min(nts, 100.0))
        nts = round(nts, 1)
        
        if nts < 50:
            label = "Synthetic Hazard"
            signal = "WARNING: SYNTHETIC SIGNAL DETECTED"
        elif nts > 80:
            label = "Grounded Human Content"
            signal = "VERIFIED: HUMAN AUTHORSHIP"
        else:
            label = "Indeterminate"
            signal = "CAUTION: MIXED SIGNALS"
            
        return {
            "nts": nts,
            "label": label,
            "signal": signal,
            "components": {
                "entropy": round(entropy, 2),
                "burstiness": round(burstiness, 2),
                "vault_proximity": round(vault_proximity, 3),
                "penalties": {
                    "entropy_deficit": round(entropy_penalty, 1),
                    "burstiness_penalty": round(burstiness_penalty, 1),
                    "vault_penalty": round(vault_penalty, 1)
                }
            }
        }

# Backward Compatibility Wrappers
def calculate_entropy(data: str) -> float:
    return TrustScorer.calculate_entropy(data)

def calculate_burstiness(text: str) -> float:
    return TrustScorer.calculate_burstiness(text)

def calculate_vault_proximity(text: str) -> float:
    return TrustScorer.calculate_vault_proximity(text)

def calculate_trust_score(entropy: float, burstiness: float, vault_proximity: float = 0.0) -> Dict[str, Any]:
    return TrustScorer.calculate_trust_score(entropy, burstiness, vault_proximity)
