import logging
import sqlite3
import os
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class NetworkGenerator:
    """
    Generates interactive network visualizations of author similarity.
    Uses stylometric distance matrices to create consensus networks.
    """

    def __init__(self, db_path: str = None):
        from src.core.config import Config
        config = Config()
        base_dir = config.get_path('storage.base_dir')
        self.db_path = db_path or str(base_dir / "storage" / "scribe_profiles.sqlite")

    def _get_all_authors(self, limit: int = 100) -> List[str]:
        """
        Retrieves all author IDs from the database.
        
        Args:
            limit: Maximum number of authors to include
            
        Returns:
            List of author IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT author_id FROM author_profiles 
            LIMIT ?
        """, (limit,))
        
        authors = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return authors

    def _calculate_distance_matrix(self, authors: List[str]) -> np.ndarray:
        """
        Calculates pairwise stylometric distances between all authors.
        
        In production, this would use actual Delta scores from StyloWrapper.
        For now, returns a symmetric random matrix for structure testing.
        
        Args:
            authors: List of author IDs
            
        Returns:
            NxN distance matrix
        """
        n = len(authors)
        # Create symmetric random matrix for testing
        # In production: would call PyStylWrapper.compare_texts() for each pair
        matrix = np.random.rand(n, n) * 2.0  # Random distances 0-2
        matrix = (matrix + matrix.T) / 2  # Make symmetric
        np.fill_diagonal(matrix, 0)  # Distance to self is 0
        
        return matrix

    def generate_network(
        self,
        threshold: float = 1.2,
        max_nodes: int = 100,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generates an interactive network visualization.
        
        Args:
            threshold: Maximum distance for edge creation (Delta < threshold = similar)
            max_nodes: Maximum number of nodes to display
            output_path: Path to save HTML file (optional)
            
        Returns:
            Path to generated HTML file
        """
        try:
            import networkx as nx
            from pyvis.network import Network
        except ImportError:
            logger.error("networkx or pyvis not installed. Run: pip install networkx pyvis")
            return ""
        
        logger.info(f"🕸️ Generating forensic network (threshold={threshold})")
        
        # 1. Get authors
        authors = self._get_all_authors(limit=max_nodes)
        
        if len(authors) < 2:
            logger.warning("Insufficient authors for network generation")
            return ""
        
        # 2. Calculate distance matrix
        distance_matrix = self._calculate_distance_matrix(authors)
        
        # 3. Build NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for author in authors:
            G.add_node(author, label=author, title=f"Author: {author}")
        
        # Add edges based on threshold
        for i, author_a in enumerate(authors):
            for j, author_b in enumerate(authors):
                if i < j:  # Avoid duplicates in undirected graph
                    distance = distance_matrix[i, j]
                    if distance < threshold:
                        # Weight for visualization: closer = thicker edge
                        weight = 1.0 / (distance + 0.1)  # Avoid division by zero
                        G.add_edge(
                            author_a, 
                            author_b, 
                            weight=weight,
                            title=f"Distance: {distance:.2f}"
                        )
        
        logger.info(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # 4. Create interactive visualization with pyvis
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#0e1117",  # Match Streamlit dark theme
            font_color="#e0e0e0",
            notebook=False
        )
        
        net.from_nx(G)
        
        # Configure physics for smooth rendering on 1660 Ti
        net.set_options("""
        {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 95
            },
            "maxVelocity": 50,
            "minVelocity": 0.1
          }
        }
        """)
        
        # 5. Save HTML
        if output_path is None:
            from src.core.config import Config
            config = Config()
            base_dir = config.get_path('storage.base_dir')
            output_path = str(base_dir / "storage" / "forensic_network.html")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        net.save_graph(output_path)
        
        logger.info(f"✅ Network saved to {output_path}")
        return output_path
