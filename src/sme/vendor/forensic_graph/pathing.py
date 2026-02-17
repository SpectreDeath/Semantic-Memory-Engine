import heapq
from typing import List, Dict, Any, Tuple, Optional

class GraphPathfinder:
    """
    Implements pathfinding algorithms for forensic relationship graphs.
    Optimized with __slots__.
    """
    __slots__ = ()

    def calculate_node_path(self, graph: Dict[str, List[Tuple[str, float]]], start_node: str, end_node: str) -> Dict[str, Any]:
        """
        Finds the shortest path between two nodes using Dijkstra's Algorithm.
        The graph is expected to be an adjacency list: {node: [(neighbor, weight), ...]}
        """
        if start_node not in graph:
            return {"error": f"Start node '{start_node}' not found in graph", "status": "Error"}
            
        distances = {node: float('inf') for node in graph}
        distances[start_node] = 0
        priority_queue = [(0, start_node)]
        previous_nodes = {node: None for node in graph}
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_node == end_node:
                break
                
            if current_distance > distances[current_node]:
                continue
                
            for neighbor, weight in graph.get(current_node, []):
                distance = current_distance + weight
                
                if distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))
                    
        if distances.get(end_node, float('inf')) == float('inf'):
            return {"path": [], "distance": float('inf'), "status": "No Path Found"}
            
        # Reconstruct path
        path = []
        curr = end_node
        while curr is not None:
            path.append(curr)
            curr = previous_nodes[curr]
        path.reverse()
        
        return {
            "path": path,
            "distance": round(float(distances[end_node]), 4),
            "status": "Success"
        }

def calculate_node_path(graph: Dict[str, List[Tuple[str, float]]], start_node: str, end_node: str) -> Dict[str, Any]:
    """Standalone wrapper for Dijkstra's pathfinding."""
    pathfinder = GraphPathfinder()
    return pathfinder.calculate_node_path(graph, start_node, end_node)
