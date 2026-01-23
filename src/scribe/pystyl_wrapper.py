import logging
import re
from collections import Counter
from typing import Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class PyStylWrapper:
    """
    Lightweight, native Python stylometry fallback.
    Implements statistical authorship measures via numpy/scipy logic.
    Memory footprint optimized for stability (<50MB).
    """

    def __init__(self):
        """Initialize the lightweight wrapper."""
        # Pre-compile regex for speed
        self._word_pattern = re.compile(r'\b\w+\b')
        logger.info("⚡ PyStylWrapper initialized")

    def _tokenize(self, text: str) -> List[str]:
        """Simple, fast tokenization dropping punctuation/case."""
        if not text:
            return []
        return [w.lower() for w in self._word_pattern.findall(text)]

    def get_word_length_distribution(self, text: str) -> Dict[int, float]:
        """
        Implements Mendenhall's Breadth.
        Returns a normalized dictionary of word lengths (1-20+ letters).
        
        Args:
            text: Input text string
            
        Returns:
            Dict mapping length (int) to frequency (float 0.0-1.0)
        """
        tokens = self._tokenize(text)
        total_tokens = len(tokens)
        
        if total_tokens == 0:
            return {}
            
        # Count lengths, cap at 20
        lengths = [min(len(t), 20) for t in tokens]
        counts = Counter(lengths)
        
        # Normalize
        dist = {l: count / total_tokens for l, count in counts.items()}
        return dict(sorted(dist.items()))

    def compare_texts(self, text_a: str, text_b: str, top_n: int = 100) -> float:
        """
        Implements Kilgariff's Chi-squared Distance.
        Uses the top N most frequent words from the combined corpus.
        
        Args:
            text_a: Reference text
            text_b: Unknown text
            top_n: Number of most frequent features to compare
            
        Returns:
            Chi-squared distance score (lower is closer match)
        """
        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)
        
        if not tokens_a or not tokens_b:
            logger.warning("Empty text provided for comparison.")
            return float('inf')

        # 1. Build combined vocabulary for feature selection
        # We need the most frequent words in the *joint* corpus (or usually the larger corpus)
        # Here we treat combined as the "language model"
        joint_counts = Counter(tokens_a) + Counter(tokens_b)
        vocab = [word for word, count in joint_counts.most_common(top_n)]
        
        # 2. Vectorize based on this vocab
        # We need counts normalized by text length
        len_a = len(tokens_a)
        len_b = len(tokens_b)
        
        count_a = Counter(tokens_a)
        count_b = Counter(tokens_b)
        
        vector_a = np.array([count_a[w] for w in vocab], dtype=np.float64)
        vector_b = np.array([count_b[w] for w in vocab], dtype=np.float64)
        
        # Normalize to frequencies (per X words, usually per 1000 or ratio)
        # Standard Chi-squared uses counts, but for different text lengths we normalize
        # Let's normalize to probability distribution
        vector_a = vector_a / len_a
        vector_b = vector_b / len_b
        
        # 3. Calculate Chi-squared distance
        # Formula: Sum( (Observed_A - Observed_B)^2 / (Observed_A + Observed_B) )
        # Note: Standard formula often compares Observed vs Expected.
        # Kilgariff's "Chi-Squared" in authorship is often simplified to:
        # Sum( (Freq_A - Freq_B)^2 / ((Freq_A + Freq_B) / 2) ) or similar variations.
        # We'll use a robust symmetric version for distance:
        # D = Sum( (A_i - B_i)^2 / (A_i + B_i) ) * 2  (Symmetric Chi-squared)
        
        numerator = (vector_a - vector_b) ** 2
        denominator = vector_a + vector_b
        
        # Avoid division by zero
        # Since vocab comes from joint_counts, denominator is 0 only if both are 0, 
        # which shouldn't happen for words in vocab unless vocab selection is weird.
        # Add epsilon for safety.
        epsilon = 1e-10
        
        chi_sq_terms = numerator / (denominator + epsilon)
        
        distance = np.sum(chi_sq_terms)
        
        return float(distance)
