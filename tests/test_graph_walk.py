"""
Comprehensive tests for gateway/graph_walk module.

Tests cover GraphWalkKNNOps (numpy backend) and GraphWalkFAISS (FAISS backend)
including node management, indexing, KNN search, graph walk retrieval, and persistence.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from gateway.graph_walk import (
    DEFAULT_VECTOR_SIZE,
    GraphWalkFAISS,
    GraphWalkKNNOps,
    GraphWalkProvider,
    KnowledgeEdge,
    KnowledgeNode,
    RetrievalResult,
    graph_walk_stats_tool,
    knn_search_tool,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_knn():
    """Create a small GraphWalkKNNOps instance with sample nodes."""
    knn = GraphWalkKNNOps(vector_size=16)
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning models require training data",
        "Forensic analysis reveals hidden patterns",
        "Neural networks excel at pattern recognition",
        "Semantic memory stores knowledge for retrieval",
    ]
    for i, text in enumerate(texts):
        knn.add_node(f"node_{i}", content=text, node_type="test", source_file=f"file_{i}.txt")
    knn.build_index()
    return knn


# ============================================================================
# KnowledgeNode / KnowledgeEdge / RetrievalResult
# ============================================================================


def test_knowledge_node_creation():
    n = KnowledgeNode(
        id="n1",
        content="test content",
        vector=[0.1] * DEFAULT_VECTOR_SIZE,
        node_type="chunk",
        source_file="/path/to/file.txt",
        trust_score=0.9,
        metadata={"key": "value"},
    )
    assert n.id == "n1"
    assert n.content == "test content"
    assert len(n.vector) == DEFAULT_VECTOR_SIZE
    assert n.node_type == "chunk"
    assert n.trust_score == 0.9
    assert n.metadata == {"key": "value"}


def test_knowledge_edge_creation():
    e = KnowledgeEdge(source_id="a", target_id="b", weight=0.8, edge_type="similar")
    assert e.source_id == "a"
    assert e.target_id == "b"
    assert e.weight == 0.8
    assert e.edge_type == "similar"


def test_retrieval_result_creation():
    node = KnowledgeNode(id="x", content="x", vector=[0.0] * DEFAULT_VECTOR_SIZE)
    r = RetrievalResult(node=node, similarity=0.95, distance=0.05)
    assert r.node is node
    assert r.similarity == 0.95
    assert r.distance == 0.05


# ============================================================================
# GraphWalkKNNOps - node management
# ============================================================================


def test_add_node_automatic_vector():
    knn = GraphWalkKNNOps(vector_size=8)
    knn.add_node("n1", content="hello world")
    assert "n1" in knn.nodes
    assert len(knn.nodes["n1"].vector) == 8
    assert not knn._indexed


def test_add_node_with_provided_vector():
    knn = GraphWalkKNNOps(vector_size=5)
    knn.add_node("n1", content="ignored", vector=[0.1, 0.2, 0.3, 0.4, 0.5])
    node = knn.nodes["n1"]
    assert node.vector == [0.1, 0.2, 0.3, 0.4, 0.5]


def test_add_nodes_from_directory(tmp_path):
    knn = GraphWalkKNNOps(vector_size=8)
    # Create a temp file
    f = tmp_path / "test.txt"
    f.write_text("Hello world. This is a test file.")
    knn.add_nodes_from_directory(str(tmp_path), extensions=[".txt"], max_nodes=10)
    assert len(knn.nodes) >= 1
    # Check chunking
    first_node = next(iter(knn.nodes.values()))
    assert len(first_node.content) <= 512


def test_add_node_vector_size_normalization():
    knn = GraphWalkKNNOps(vector_size=5)
    # Vector too short
    knn.add_node("short", content="x", vector=[1, 2])
    assert len(knn.nodes["short"].vector) == 5
    assert knn.nodes["short"].vector[2:] == [0.0, 0.0, 0.0]
    # Vector too long
    knn.add_node("long", content="x", vector=list(range(10)))
    assert len(knn.nodes["long"].vector) == 5


# ============================================================================
# GraphWalkKNNOps - indexing and search
# ============================================================================


def test_build_index(sample_knn):
    sample_knn.build_index()
    assert sample_knn._indexed is True
    assert len(sample_knn.node_ids) == len(sample_knn.nodes)
    assert sample_knn.vector_matrix.shape[0] == len(sample_knn.nodes)


def test_knn_search_returns_sorted(sample_knn):
    results = sample_knn.knn_search("machine learning", k=3)
    assert len(results) <= 3
    # Verify sorted by similarity descending
    sims = [r.similarity for r in results]
    assert sims == sorted(sims, reverse=True)
    # All distances should be 1 - similarity
    for r in results:
        assert abs(r.distance - (1 - r.similarity)) < 1e-6


def test_knn_search_min_similarity_threshold(sample_knn):
    # Threshold > 1.0 is impossible, guarantees zero results
    results = sample_knn.knn_search("machine learning", k=5, min_similarity=2.0)
    assert len(results) == 0


def test_knn_search_empty_index():
    knn = GraphWalkKNNOps()
    results = knn.knn_search("test")
    assert results == []


def test_knn_search_autobuild_index(sample_knn):
    # Build index not called explicitly
    sample_knn._indexed = False
    results = sample_knn.knn_search("test")
    assert sample_knn._indexed is True


# ============================================================================
# GraphWalkKNNOps - graph walk retrieval
# ============================================================================


def test_graph_walk_retrieval_basic(sample_knn):
    results = sample_knn.graph_walk_retrieval("knowledge", k=3, trust_threshold=0.0)
    assert len(results) <= 3
    for r in results:
        assert "content" in r
        assert "similarity" in r
        assert "trust_score" in r


def test_graph_walk_retrieval_respects_trust_threshold():
    knn = GraphWalkKNNOps()
    knn.add_node("low_trust", content="test", trust_score=0.1)
    knn.add_node("high_trust", content="test", trust_score=0.9)
    knn.build_index()
    # low_trust should be filtered
    results = knn.graph_walk_retrieval("test", k=2, trust_threshold=0.5)
    ids = [r["node_id"] for r in results]
    assert "high_trust" in ids
    assert "low_trust" not in ids


# ============================================================================
# GraphWalkKNNOps - persistence
# ============================================================================


def test_save_and_load_index(tmp_path):
    knn = GraphWalkKNNOps(vector_size=8)
    knn.add_node("a", content="alpha", trust_score=0.7)
    knn.add_node("b", content="beta", trust_score=0.8)
    knn.build_index()

    out = tmp_path / "idx.json"
    knn.save_index(str(out))

    knn2 = GraphWalkKNNOps(vector_size=8)
    knn2.load_index(str(out))

    assert len(knn2.nodes) == 2
    assert "a" in knn2.nodes
    assert knn2.nodes["a"].trust_score == 0.7
    # Rebuild index and search works
    knn2.build_index()
    results = knn2.knn_search("alpha", k=1)
    assert len(results) == 1
    assert results[0].node.id == "a"


# ============================================================================
# GraphWalkKNNOps - stats and helpers
# ============================================================================


def test_get_stats():
    knn = GraphWalkKNNOps()
    knn.add_node("x", content="x", node_type="chunk")
    knn.add_node("y", content="y", node_type="doc")
    stats = knn.get_stats()
    assert stats["total_nodes"] == 2
    assert stats["vector_size"] == DEFAULT_VECTOR_SIZE
    assert stats["node_types"]["chunk"] == 1
    assert stats["node_types"]["doc"] == 1
    assert stats["indexed"] is False


def test_chunk_text():
    knn = GraphWalkKNNOps()
    text = "a b c d e f g"
    chunks = knn._chunk_text(text, chunk_size=3)
    assert len(chunks) == 5  # character-based splitting: "a b", " c ", "d e", " f ", "g"
    assert chunks[0]["text"] == "a b"


def test_text_to_vector():
    knn = GraphWalkKNNOps(vector_size=10)
    vec = knn._text_to_vector("hello")
    assert len(vec) == 10
    # Vector elements are floats
    assert all(isinstance(x, float) for x in vec)


# ============================================================================
# GraphWalkProvider wrapper
# ============================================================================


def test_graphwalk_provider_retrieve():
    knn = GraphWalkKNNOps(vector_size=DEFAULT_VECTOR_SIZE)
    knn.add_node("n1", content="forensic analysis")
    knn.build_index()
    provider = GraphWalkProvider(knn=knn)
    results = provider.retrieve("forensic analysis", k=2)
    assert len(results) <= 2
    assert any(r["node_id"] == "n1" for r in results)


def test_graphwalk_provider_build_prompt_augmentation():
    knn = GraphWalkKNNOps(vector_size=DEFAULT_VECTOR_SIZE)
    knn.add_node("n1", content="Forensic analysis")
    knn.build_index()
    provider = GraphWalkProvider(knn=knn)
    prompt = provider.build_prompt_with_knowledge("forensic analysis", k=1, max_context_tokens=100)
    assert "Forensic analysis" in prompt
    assert "## Retrieved Knowledge:" in prompt


# ============================================================================
# MCP Tools
# ============================================================================


def test_knn_search_tool_basic():
    result = knn_search_tool("query", k=3)
    assert result["status"] == "success"  # No knowledge dir, but tool should still execute
    assert result["result_count"] == 0


def test_graph_walk_stats_tool():
    result = graph_walk_stats_tool()
    assert "status" in result
    # With no custom dir, uses default empty state
    if result["status"] == "success":
        assert "stats" in result


# ============================================================================
# FAISS backend (conditional)
# ============================================================================

# Check FAISS availability
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not installed")
class TestGraphWalkFAISS:
    """Test FAISS-accelerated backend (requires faiss-cpu)."""

    def test_faiss_add_and_build(self):
        knn = GraphWalkFAISS(vector_size=16)
        knn.add_node("a", content="alpha")
        knn.add_node("b", content="beta")
        knn.build_index()
        assert knn._indexed
        assert knn._index.ntotal == 2

    def test_faiss_knn_search(self):
        knn = GraphWalkFAISS(vector_size=16)
        knn.add_node("a", content="alpha beta gamma")
        knn.add_node("b", content="delta epsilon zeta")
        knn.build_index()
        results = knn.knn_search("alpha", k=1)
        assert len(results) == 1
        assert results[0].node.id == "a"

    def test_faiss_save_load(self, tmp_path):
        knn = GraphWalkFAISS(vector_size=16)
        knn.add_node("a", content="test", trust_score=0.9)
        knn.build_index()
        out_json = tmp_path / "idx.json"
        knn.save_index(str(out_json))
        # Load into new instance
        knn2 = GraphWalkFAISS(vector_size=16)
        knn2.load_index(str(out_json))
        assert len(knn2.nodes) == 1
        assert knn2.nodes["a"].trust_score == 0.9
        # Index built after load
        assert knn2._indexed
        assert knn2._index.ntotal == 1

    def test_faiss_ivf_enabled(self):
        knn = GraphWalkFAISS(use_ivf=True, nlist=10)
        assert knn.use_ivf is True

    def test_faiss_stats(self):
        knn = GraphWalkFAISS()
        knn.add_node("x", content="x")
        knn.build_index()
        stats = knn.get_stats()
        assert stats["total_nodes"] == 1
        assert stats["indexed"] is True
        assert "faiss_backend" in stats


def test_faiss_unavailable_stub():
    """When FAISS not installed, GraphWalkFAISS should raise ImportError on instantiation."""
    if FAISS_AVAILABLE:
        pytest.skip("FAISS is installed; stub test not applicable")
    from gateway.graph_walk import GraphWalkFAISS

    with pytest.raises(ImportError):
        GraphWalkFAISS()
