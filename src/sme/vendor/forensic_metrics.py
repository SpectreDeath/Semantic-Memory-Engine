import numpy as np
from typing import Tuple

def calculate_cosine_delta(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculates the 'Cosine Delta', a stylometric distance metric that 
    combines Burrows' Delta logic with Cosine Similarity.
    
    Optimized for Python 3.10+ using NumPy.
    """
    v1 = np.asarray(v1, dtype=float)
    v2 = np.asarray(v2, dtype=float)
    
    # Cosine Similarity component
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        cosine_sim = 0.0
    else:
        cosine_sim = dot_product / (norm_v1 * norm_v2)
        
    # Delta component (Manhattan distance on normalized vectors)
    # We use (1 - cosine_sim) as a distance and combine with Manhattan
    manhattan_dist = np.mean(np.abs(v1 - v2))
    
    # Combined Forensic Metric: Weighted combination of angular and linear distance
    return float(0.5 * (1.0 - cosine_sim) + 0.5 * manhattan_dist)

def calculate_symmetrized_kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """
    Calculates the Symmetrized KL Divergence (also known as Jensen-Shannon Divergence 
    without the square root, or simply a balanced KL).
    
    Measures the informational divergence between two probability distributions.
    """
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    
    # Normalize to probability distributions
    p = p / (np.sum(p) + 1e-12)
    q = q / (np.sum(q) + 1e-12)
    
    epsilon = 1e-12
    p = np.clip(p, epsilon, 1.0)
    q = np.clip(q, epsilon, 1.0)
    
    # KL(P||Q)
    kl_pq = np.sum(p * np.log(p / q))
    # KL(Q||P)
    kl_qp = np.sum(q * np.log(q / p))
    
    # Symmetrized version
    return float((kl_pq + kl_qp) / 2.0)
