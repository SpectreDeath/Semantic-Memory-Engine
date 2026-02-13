import numpy as np
from typing import Dict, List, Tuple

def dict_to_vectors(d1: Dict[str, float], d2: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Converts two frequency dictionaries into aligned NumPy vectors.
    """
    all_keys = sorted(set(d1.keys()) | set(d2.keys()))
    v1 = np.array([d1.get(k, 0.0) for k in all_keys])
    v2 = np.array([d2.get(k, 0.0) for k in all_keys])
    return v1, v2

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculates the cosine similarity between two vectors.
    Optimized for performance on hardware with vectorized operations.
    """
    dot_product = np.dot(vec1, vec2)
    norm_v1 = np.linalg.norm(vec1)
    norm_v2 = np.linalg.norm(vec2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return float(dot_product / (norm_v1 * norm_v2))
