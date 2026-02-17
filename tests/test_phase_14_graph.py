import sys
import os
from pathlib import Path
import json
import numpy as np

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_graph

def test_forensic_graph():
    print("[*] Testing Forensic Graph (Pathing & Centrality) algorithms...")
    
    # 1. Dijkstra Pathfinding Test
    # Adjacency list: {node: [(neighbor, weight), ...]}
    graph = {
        "A": [("B", 1.0), ("C", 4.0)],
        "B": [("C", 2.0), ("D", 5.0)],
        "C": [("D", 1.0)],
        "D": []
    }
    
    res_path = forensic_graph.calculate_node_path(graph, "A", "D")
    print(f"[+] Dijkstra Path: {res_path['path']} (Distance: {res_path['distance']})")
    assert res_path['path'] == ["A", "B", "C", "D"]
    assert res_path['distance'] == 4.0
    
    # 2. Eigenvector Centrality Test
    # Star graph: node 0 connected to 1, 2, 3
    # Adjacency matrix:
    #   0 1 1 1
    #   1 0 0 0
    #   1 0 0 0
    #   1 0 0 0
    adj_matrix = [
        [0, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 0]
    ]
    labels = ["Hub", "Leaf1", "Leaf2", "Leaf3"]
    
    res_centrality = forensic_graph.identify_central_hubs(adj_matrix, labels)
    print(f"[+] Top Hub: {res_centrality['top_hubs'][0]}")
    assert res_centrality['top_hubs'][0] == "Hub"
    assert res_centrality['centrality_scores']["Hub"] > res_centrality['centrality_scores']["Leaf1"]
    
    print("[+] All Phase 14 algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_forensic_graph()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
