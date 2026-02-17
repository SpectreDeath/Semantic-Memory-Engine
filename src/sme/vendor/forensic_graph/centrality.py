import numpy as np
from typing import List, Dict, Any, Tuple

class GraphCentrality:
    """
    Analyzes node influence and centrality in forensic clusters.
    Optimized with __slots__.
    """
    __slots__ = ()

    def identify_central_hubs(self, adjacency_matrix: List[List[float]], node_labels: List[str], max_iter: int = 100, tol: float = 1e-6) -> Dict[str, Any]:
        """
        Identifies influential nodes using Power Iteration (Eigenvector Centrality).
        Simplified version of PageRank without the damping factor.
        """
        matrix = np.array(adjacency_matrix, dtype=float)
        n = matrix.shape[0]
        
        if n == 0:
            return {"hubs": [], "status": "Empty Matrix"}
            
        # Initialize centrality vector
        v = np.ones(n) / n
        
        for i in range(max_iter):
            v_next = np.dot(matrix, v)
            
            # Normalize to prevent magnitude explosion
            norm = np.linalg.norm(v_next)
            if norm == 0:
                break
            v_next = v_next / norm
            
            # Check convergence
            if np.linalg.norm(v - v_next) < tol:
                v = v_next
                break
            v = v_next
            
        # Pair with labels and sort
        centrality_scores = {label: float(score) for label, score in zip(node_labels, v)}
        sorted_hubs = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "centrality_scores": centrality_scores,
            "top_hubs": [hub[0] for hub in sorted_hubs[:5]],
            "iterations": i + 1,
            "status": "Success"
        }

def identify_central_hubs(adjacency_matrix: List[List[float]], node_labels: List[str]) -> Dict[str, Any]:
    """Standalone wrapper for Hub identification."""
    analyzer = GraphCentrality()
    return analyzer.identify_central_hubs(adjacency_matrix, node_labels)
