"""
Graph Walk Navigator - KNN-based knowledge retrieval.

This is Step 3.1 of Phase 3 - implements a k-Nearest Neighbor search on local
embeddings to act as an FFN-style knowledge look-up, decoupling Attention
from the Knowledge Store.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger("lawnmower.graph_walk")

DEFAULT_VECTOR_SIZE = 128

# Optional FAISS support for >10k nodes
try:
    import faiss

    FAISS_AVAILABLE = True
    logger.info("FAISS available - using accelerated indexing for >10k nodes")
except ImportError:
    FAISS_AVAILABLE = False
    logger.info("FAISS not available - falling back to numpy indexing")


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""

    id: str
    content: str
    vector: list[float]
    node_type: str = "chunk"
    source_file: str = ""
    trust_score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeEdge:
    """An edge connecting knowledge nodes."""

    source_id: str
    target_id: str
    weight: float = 1.0
    edge_type: str = "references"


@dataclass
class RetrievalResult:
    """Result from KNN retrieval."""

    node: KnowledgeNode
    similarity: float
    distance: float = 0.0


class GraphWalkKNNOps:
    """
    Implements k-Nearest Neighbor search on local knowledge embeddings.

    Acts as an external "FFN" (Feed-Forward Network) knowledge look-up
    that decouples retrieval from the LLM's attention mechanism.
    """

    def __init__(self, vector_size: int = DEFAULT_VECTOR_SIZE, index_file: str | None = None):
        self.vector_size = vector_size
        self.index_file = index_file
        self.nodes: dict[str, KnowledgeNode] = {}
        self.node_vectors: list[np.ndarray] = []
        self.node_ids: list[str] = []
        self._indexed = False

    def add_node(
        self,
        node_id: str,
        content: str,
        vector: list[float] | None = None,
        node_type: str = "chunk",
        source_file: str = "",
        trust_score: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ):
        """Add a knowledge node."""
        if vector is None:
            vector = self._text_to_vector(content)

        if len(vector) < self.vector_size:
            vector.extend([0.0] * (self.vector_size - len(vector)))
        elif len(vector) > self.vector_size:
            vector = vector[: self.vector_size]

        node = KnowledgeNode(
            id=node_id,
            content=content,
            vector=vector,
            node_type=node_type,
            source_file=source_file,
            trust_score=trust_score,
            metadata=metadata or {},
        )

        self.nodes[node_id] = node
        self._indexed = False

    def add_nodes_from_directory(
        self, directory: str, extensions: list[str] | None = None, max_nodes: int = 1000
    ):
        """Add knowledge nodes from all files in a directory."""
        if extensions is None:
            extensions = [".txt", ".md", ".log"]
        count = 0

        for root, _, files in os.walk(directory):
            for file in files:
                if not any(file.endswith(ext) for ext in extensions):
                    continue

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    chunks = self._chunk_text(content, chunk_size=512)

                    for i, chunk in enumerate(chunks):
                        node_id = f"{file}_{i}"
                        self.add_node(
                            node_id=node_id,
                            content=chunk["text"],
                            node_type="chunk",
                            source_file=file_path,
                            trust_score=0.8,
                            metadata={
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                            },
                        )
                        count += 1

                        if count >= max_nodes:
                            logger.warning(f"Reached max_nodes limit: {max_nodes}")
                            return

                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")

    def _chunk_text(self, text: str, chunk_size: int = 512) -> list[dict[str, Any]]:
        """Split text into chunks."""
        chunks = []

        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            if chunk.strip():
                chunks.append({"text": chunk, "index": len(chunks)})

            if i + chunk_size >= len(text):
                break

        return chunks

    def _text_to_vector(self, text: str) -> list[float]:
        """Convert text to optimized embedding vector using n-gram features."""
        if not text:
            return [0.0] * self.vector_size

        # Use word + character n-grams for richer representation
        words = text.lower().split()

        # Character 3-gram counts (faster than word tokens)
        char_ngrams = {}
        for i in range(len(text) - 2):
            ngram = text[i : i + 3].lower()
            char_ngrams[ngram] = char_ngrams.get(ngram, 0) + 1

        # Word unigrams
        for w in words:
            char_ngrams[w] = char_ngrams.get(w, 0) + 1

        # Normalize to vector
        total = sum(char_ngrams.values())
        if total == 0:
            return [0.0] * self.vector_size

        # Create sparse vector for efficiency
        indices = []
        values = []
        for idx, (hash_key, count) in enumerate(char_ngrams.items()):
            indices.append(hash(text) % self.vector_size)
            values.append(count / total)
            if len(indices) >= self.vector_size:
                break

        # Fill vector
        vector = [0.0] * self.vector_size
        for i, v in zip(indices[: self.vector_size], values[: self.vector_size], strict=True):
            vector[i % self.vector_size] += v

        return vector[: self.vector_size]

    def build_index(self):
        """Build optimized index with pre-normalized vectors."""
        self.node_ids = list(self.nodes.keys())

        # Pre-compute normalized vectors for faster search
        self.node_vectors = []
        self.node_norms = []

        for nid in self.node_ids:
            vec = np.array(self.nodes[nid].vector)
            norm = np.linalg.norm(vec)
            # Store normalized to avoid repeated normalization
            if norm > 0:
                vec = vec / norm
            self.node_vectors.append(vec)
            self.node_norms.append(norm)

        # Convert to single matrix for batch operations
        self.vector_matrix = (
            np.array(self.node_vectors)
            if self.node_vectors
            else np.array([]).reshape(0, self.vector_size)
        )

        self._indexed = True
        logger.info(
            f"Built optimized index for {len(self.node_ids)} nodes ({self.vector_matrix.shape})"
        )

    def knn_search(
        self, query: str, k: int = 5, min_similarity: float = 0.0
    ) -> list[RetrievalResult]:
        """
        Perform optimized k-Nearest Neighbor search with batch operations.

        Args:
            query: Query text
            k: Number of neighbors to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of RetrievalResult objects sorted by similarity
        """
        if not self.nodes:
            return []

        if not self._indexed:
            self.build_index()

        # Vectorize query
        query_vector = np.array(self._text_to_vector(query)[: self.vector_size])

        # Pre-normalize query
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return []

        query_vector_norm = query_vector / query_norm

        # Batch compute all similarities at once (faster than loop)
        if self.vector_matrix.shape[0] > 0:
            # Matrix multiplication for all vectors at once
            similarities = np.dot(self.vector_matrix, query_vector_norm)

            # Get top-k indices
            top_k_indices = np.argsort(similarities)[-k:][::-1]

            results = []
            for idx in top_k_indices:
                sim = float(similarities[idx])
                if sim < min_similarity:
                    continue

                node_id = self.node_ids[idx]
                node = self.nodes[node_id]
                dist = 1.0 - sim

                results.append(
                    RetrievalResult(
                        node=node,
                        similarity=sim,
                        distance=dist,
                    )
                )

        results.sort(key=lambda x: x.similarity, reverse=True)

        return results[:k]

    def graph_walk_retrieval(
        self, query: str, k: int = 5, max_hops: int = 3, trust_threshold: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        Perform graph walk retrieval with trust scoring.

        Args:
            query: Query text
            k: Number of results
            max_hops: Maximum hops in the graph
            trust_threshold: Minimum trust score to consider

        Returns:
            List of retrieved chunks with metadata
        """
        initial_results = self.knn_search(query, k=k * 2, min_similarity=trust_threshold)

        if not initial_results:
            return []

        walked_results = []
        seen_content: set[str] = set()

        for result in initial_results:
            content_hash = hash(result.node.content)

            if content_hash in seen_content:
                continue

            if result.node.trust_score < trust_threshold:
                continue

            seen_content.add(content_hash)

            walked_results.append(
                {
                    "content": result.node.content,
                    "similarity": round(result.similarity, 4),
                    "distance": round(result.distance, 4),
                    "trust_score": result.node.trust_score,
                    "source": result.node.source_file,
                    "node_type": result.node.node_type,
                    "node_id": result.node.id,
                }
            )

            if len(walked_results) >= k:
                break

        return walked_results

    def save_index(self, output_path: str):
        """Save the index to disk."""
        data = {
            "vector_size": self.vector_size,
            "nodes": [
                {
                    "id": node.id,
                    "content": node.content,
                    "vector": node.vector,
                    "node_type": node.node_type,
                    "source_file": node.source_file,
                    "trust_score": node.trust_score,
                    "metadata": node.metadata,
                }
                for node in self.nodes.values()
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        logger.info(f"Saved index with {len(self.nodes)} nodes to {output_path}")

    def load_index(self, input_path: str):
        """Load the index from disk."""
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)

        self.vector_size = data.get("vector_size", DEFAULT_VECTOR_SIZE)

        for node_data in data.get("nodes", []):
            self.add_node(
                node_id=node_data["id"],
                content=node_data["content"],
                vector=node_data["vector"],
                node_type=node_data.get("node_type", "chunk"),
                source_file=node_data.get("source_file", ""),
                trust_score=node_data.get("trust_score", 1.0),
                metadata=node_data.get("metadata", {}),
            )

        self.build_index()
        logger.info(f"Loaded index with {len(self.nodes)} nodes from {input_path}")

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        node_types: dict[str, int] = {}
        trust_scores: list[float] = []

        for node in self.nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
            trust_scores.append(node.trust_score)

        return {
            "total_nodes": len(self.nodes),
            "vector_size": self.vector_size,
            "node_types": node_types,
            "avg_trust_score": sum(trust_scores) / len(trust_scores) if trust_scores else 0,
            "indexed": self._indexed,
        }


class GraphWalkProvider:
    """
    Provider that wraps an LLM with Graph Walk knowledge retrieval.

    Intercepts prompts, retrieves relevant knowledge via KNN,
    and augments the prompt before passing to the LLM.
    """

    def __init__(self, knn: GraphWalkKNNOps | None = None, knowledge_directory: str | None = None):
        self.knn = knn or GraphWalkKNNOps()

        if knowledge_directory:
            self.knn.add_nodes_from_directory(knowledge_directory)
            self.knn.build_index()

    def retrieve(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Retrieve knowledge for a query."""
        return self.knn.graph_walk_retrieval(query, k=k)

    def build_prompt_with_knowledge(
        self, user_prompt: str, k: int = 5, max_context_tokens: int = 2000
    ) -> str:
        """Build a prompt augmented with retrieved knowledge."""
        results = self.retrieve(user_prompt, k=k)

        if not results:
            return user_prompt

        knowledge_context = "\n\n## Retrieved Knowledge:\n"

        for r in results:
            knowledge_context += f"- {r['content'][:200]}... (trust: {r['trust_score']:.2f})\n"

        return f"{user_prompt}\n{knowledge_context}"


def knn_search_tool(query: str, k: int = 5, knowledge_dir: str | None = None) -> dict[str, Any]:
    """MCP Tool: Perform KNN search on knowledge."""
    try:
        knn = GraphWalkKNNOps()

        if knowledge_dir and os.path.exists(knowledge_dir):
            knn.add_nodes_from_directory(knowledge_dir)
            knn.build_index()

        results = knn.graph_walk_retrieval(query, k=k)

        return {
            "status": "success",
            "query": query,
            "results": results,
            "result_count": len(results),
            "stats": knn.get_stats(),
        }

    except Exception as e:
        logger.exception(f"KNN search failed: {e}")
        return {"status": "error", "error": str(e)}


def graph_walk_stats_tool() -> dict[str, Any]:
    """MCP Tool: Get Graph Walk statistics."""
    try:
        knn = GraphWalkKNNOps()
        return {"status": "success", "stats": knn.get_stats()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# FAISS-Backed variant for >10k node scaling
# ---------------------------------------------------------------------------

if FAISS_AVAILABLE:
    import faiss

    class GraphWalkFAISS(GraphWalkKNNOps):
        """
        FAISS-accelerated KNN operations for large knowledge graphs (>10k nodes).

        Uses Facebook AI Similarity Search (FAISS) for O(log n) approximate nearest
        neighbor search vs O(n) brute-force numpy. Provides 10-100x speedup on
        10k+ node datasets with minimal accuracy trade-off.
        """

        def __init__(
            self,
            vector_size: int = DEFAULT_VECTOR_SIZE,
            index_file: str | None = None,
            *,
            use_ivf: bool = False,
            nlist: int = 100,
            nprobe: int = 10,
        ):
            super().__init__(vector_size, index_file)
            self.use_ivf = use_ivf and FAISS_AVAILABLE
            self.nlist = nlist
            self.nprobe = nprobe
            self._index: faiss.Index | None = None
            self._id_map: dict[int, str] = {}  # FAISS index -> node_id

        def build_index(self) -> None:
            """Build FAISS index for fast similarity search."""
            if not self.nodes:
                logger.warning("No nodes to index")
                return

            self.node_ids = list(self.nodes.keys())

            # Build vector matrix (same as numpy version)
            vectors = []
            for nid in self.node_ids:
                vec = np.array(self.nodes[nid].vector, dtype=np.float32)
                vec = vec / (np.linalg.norm(vec) + 1e-8)
                vectors.append(vec)

            vectors_np = np.stack(vectors).astype(np.float32)

            # Create FAISS index
            d = self.vector_size
            if self.use_ivf and len(vectors_np) >= self.nlist * 10:
                # IVF index for large datasets (clustering-based)
                quantizer = faiss.IndexFlatIP(d)
                self._index = faiss.IndexIVFFlat(quantizer, d, self.nlist)
                self._index.train(vectors_np)
                logger.info(f"Using FAISS IVF index (nlist={self.nlist}, nprobe={self.nprobe})")
            else:
                # Flat index - exact search, still GPU-accelerated
                self._index = faiss.IndexFlatIP(d)
                logger.info("Using FAISS Flat index (exact search)")

            # Add vectors to index
            self._index.add(vectors_np)
            self._id_map = {i: nid for i, nid in enumerate(self.node_ids)}
            self._indexed = True

            logger.info(
                f"Built FAISS index: {self._index.ntotal} vectors, d={d}, "
                f"backend={'IVF' if self.use_ivf else 'Flat'}"
            )

        def knn_search(
            self, query: str, k: int = 5, min_similarity: float = 0.0
        ) -> list[RetrievalResult]:
            """FAISS-accelerated KNN search."""
            if not self.nodes:
                return []

            if not self._indexed or self._index is None:
                self.build_index()

            # Vectorize query
            query_vec = np.array(self._text_to_vector(query)[: self.vector_size], dtype=np.float32)
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0:
                return []
            query_vec = query_vec.reshape(1, -1).astype(np.float32)
            query_vec = query_vec / (query_norm + 1e-8)

            # Search with FAISS
            _, indices = self._index.search(query_vec, min(k, len(self.node_ids)))

            results = []
            for idx in indices[0]:
                if idx < 0 or idx >= len(self.node_ids):
                    continue
                nid = self._id_map.get(int(idx), self.node_ids[int(idx)])
                node = self.nodes[nid]

                # Recompute similarity (FAISS returns inner product which is cosine for normalized)
                node_vec = np.array(node.vector, dtype=np.float32)
                node_vec = node_vec / (np.linalg.norm(node_vec) + 1e-8)
                sim = float(np.dot(query_vec.flatten(), node_vec))

                if sim < min_similarity:
                    continue

                results.append(RetrievalResult(node=node, similarity=sim, distance=1.0 - sim))

            results.sort(key=lambda x: x.similarity, reverse=True)
            return results[:k]

        def save_index(self, output_path: str) -> None:
            """Save FAISS index to disk."""
            if self._index is None:
                raise RuntimeError("No index to save - call build_index() first")

            # Save FAISS index
            faiss_path = output_path.replace(".json", ".faissindex")
            faiss.write_index(self._index, faiss_path)

            # Save metadata (node_ids, vectors, config)
            data = {
                "vector_size": self.vector_size,
                "node_ids": self.node_ids,
                "nodes": [
                    {
                        "id": node.id,
                        "content": node.content,
                        "vector": node.vector,
                        "node_type": node.node_type,
                        "source_file": node.source_file,
                        "trust_score": node.trust_score,
                        "metadata": node.metadata,
                    }
                    for node in self.nodes.values()
                ],
                "faiss_backend": "ivf" if self.use_ivf else "flat",
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            logger.info(f"Saved FAISS index ({self._index.ntotal} vectors) to {faiss_path}")

        def load_index(self, input_path: str) -> None:
            """Load FAISS index from disk."""
            faiss_path = input_path.replace(".json", ".faissindex")
            if not os.path.exists(faiss_path):
                raise FileNotFoundError(f"FAISS index file not found: {faiss_path}")

            # Load FAISS index
            self._index = faiss.read_index(faiss_path)
            self._indexed = True
            d = self._index.d

            # Load metadata
            with open(input_path, encoding="utf-8") as f:
                data = json.load(f)

            self.vector_size = data.get("vector_size", d)
            self.node_ids = data.get("node_ids", [])
            self._id_map = {i: nid for i, nid in enumerate(self.node_ids)}

            # Rebuild nodes dict
            self.nodes = {}
            for node_data in data.get("nodes", []):
                from dataclasses import dataclass

                # Recreate KnowledgeNode
                node = KnowledgeNode(
                    id=node_data["id"],
                    content=node_data["content"],
                    vector=node_data["vector"],
                    node_type=node_data.get("node_type", "chunk"),
                    source_file=node_data.get("source_file", ""),
                    trust_score=node_data.get("trust_score", 1.0),
                    metadata=node_data.get("metadata", {}),
                )
                self.nodes[node.id] = node

            logger.info(
                f"Loaded FAISS index: {self._index.ntotal} vectors, d={d}, "
                f"backend={data.get('faiss_backend', 'flat')}"
            )

    def knn_search_tool_faiss(
        query: str,
        k: int = 5,
        knowledge_dir: str | None = None,
        *,
        use_ivf: bool = False,
    ) -> dict[str, Any]:
        """MCP Tool: FAISS-accelerated KNN search for >10k nodes."""
        try:
            if not FAISS_AVAILABLE:
                return {"error": "FAISS not installed. Install with: pip install faiss-cpu"}

            knn = GraphWalkFAISS(use_ivf=use_ivf)
            if knowledge_dir and os.path.exists(knowledge_dir):
                knn.add_nodes_from_directory(knowledge_dir)
                knn.build_index()

            results = knn.knn_search(query, k=k)
            return {
                "status": "success",
                "query": query,
                "results": results,
                "result_count": len(results),
                "backend": "faiss",
                "stats": knn.get_stats(),
            }
        except Exception as e:
            logger.exception(f"FAISS KNN search failed: {e}")
            return {"status": "error", "backend": "faiss", "error": str(e)}


else:
    # FAISS not available - create stubs
    class GraphWalkFAISS:  # type: ignore[no-redef]
        """FAISS not available in this environment."""

        def __init__(self, *args: Any, **kwargs: Any):
            raise ImportError("FAISS is not installed. Install with: pip install faiss-cpu")

    def knn_search_tool_faiss(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"status": "error", "error": "FAISS not available"}
