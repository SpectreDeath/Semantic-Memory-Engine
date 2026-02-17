import numpy as np
from typing import List, Union, Dict, Any

class SignalSequenceAnalyzer:
    """
    Analyzes similarity between time-series sequences.
    Optimized with __slots__.
    """
    __slots__ = ()

    def calculate_sequence_similarity(self, seq1: Union[List[float], np.ndarray], seq2: Union[List[float], np.ndarray]) -> Dict[str, Any]:
        """
        Calculates similarity using a simplified Dynamic Time Warping (DTW) algorithm.
        Returns the alignment cost (lower is more similar) and a normalized similarity score.
        """
        s1 = np.asarray(seq1, dtype=float)
        s2 = np.asarray(seq2, dtype=float)
        
        n, m = len(s1), len(s2)
        if n == 0 or m == 0:
            return {"similarity_score": 0.0, "alignment_cost": float('inf'), "status": "Empty Sequence"}
            
        # Initialize DTW matrix
        dtw_matrix = np.full((n + 1, m + 1), fill_value=np.inf)
        dtw_matrix[0, 0] = 0
        
        # Calculate DTW cost
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(s1[i - 1] - s2[j - 1])
                dtw_matrix[i, j] = cost + min(dtw_matrix[i - 1, j],    # Insertion
                                             dtw_matrix[i, j - 1],    # Deletion
                                             dtw_matrix[i - 1, j - 1]) # Match
                                             
        alignment_cost = float(dtw_matrix[n, m])
        
        # Normalize similarity (using sequence length as scale)
        # Similarity = 1 / (1 + cost/max_len)
        max_len = max(n, m)
        similarity_score = 1.0 / (1.0 + (alignment_cost / max_len))
        
        return {
            "alignment_cost": round(alignment_cost, 4),
            "similarity_score": round(similarity_score, 4),
            "sequence_lengths": [n, m],
            "status": "Success"
        }

def calculate_sequence_similarity(seq1: List[float], seq2: List[float]) -> Dict[str, Any]:
    """Standalone wrapper for DTW similarity."""
    analyzer = SignalSequenceAnalyzer()
    return analyzer.calculate_sequence_similarity(seq1, seq2)
