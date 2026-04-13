import json
import logging
import math
from collections.abc import Callable
from typing import Any

import numpy as np

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("SME.SemanticRAG")

CHUNK_STRATEGIES = {
    "code": {"size": 512, "overlap": 50, "description": "512 chars, 50 overlap"},
    "docs": {"size": 1024, "overlap": 100, "description": "1024 chars, 100 overlap"},
    "conversation": {"size": 0, "overlap": 0, "description": "Full messages as chunks"},
}

SIMILARITY_THRESHOLDS = {
    "exact_match": 0.95,
    "high_similarity": 0.85,
    "relevant": 0.70,
    "loose": 0.50,
}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not a or not b:
        return 0.0

    a = np.array(a)
    b = np.array(b)

    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot / (norm_a * norm_b))


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[dict[str, Any]]:
    """Split text into overlapping chunks."""
    if not text:
        return []

    chunks = []
    chars = list(text)
    step = chunk_size - overlap

    for i in range(0, len(chars), step):
        chunk_chars = chars[i : i + chunk_size]
        chunk_text = "".join(chunk_chars)

        if chunk_text.strip():
            chunks.append(
                {
                    "text": chunk_text,
                    "index": len(chunks),
                    "start_char": i,
                    "end_char": min(i + chunk_size, len(chars)),
                    "length": len(chunk_text),
                }
            )

        if i + chunk_size >= len(chars):
            break

    return chunks


def suggest_chunk_strategy(content_type: str) -> dict[str, Any]:
    """Recommend chunk strategy based on content type."""
    if content_type.lower() in ["code", "python", "javascript", "typescript"]:
        return CHUNK_STRATEGIES["code"]

    if content_type.lower() in ["docs", "documentation", "readme"]:
        return CHUNK_STRATEGIES["docs"]

    if content_type.lower() in ["chat", "conversation", "messages"]:
        return CHUNK_STRATEGIES["conversation"]

    return CHUNK_STRATEGIES["docs"]


def rerank_results(
    query: str, results: list[dict[str, Any]], top_k: int = 5
) -> list[dict[str, Any]]:
    """Re-rank retrieval results using simple relevance scoring."""
    query_terms = set(query.lower().split())

    scored = []
    for r in results:
        text = r.get("text", "").lower()
        text_terms = set(text.split())

        overlap = len(query_terms & text_terms)
        score = overlap / (len(query_terms) + len(text_terms) + 1)

        scored.append({**r, "rerank_score": score})

    scored.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

    return scored[:top_k]


class SemanticRAGExtension(BasePlugin):
    """Semantic RAG optimization extension."""

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Semantic RAG Optimizer initialized")

    def get_tools(self) -> list[Callable]:
        return [
            self.chunk_text,
            self.analyze_retrieval,
            self.tune_similarity,
            self.suggest_strategy,
            self.rerank_results,
        ]

    async def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> str:
        """Split text into overlapping chunks."""
        chunks = chunk_text(text, chunk_size, overlap)

        return json.dumps(
            {
                "original_length": len(text),
                "chunk_count": len(chunks),
                "chunk_size": chunk_size,
                "overlap": overlap,
                "chunks": chunks,
            },
            indent=2,
        )

    async def analyze_retrieval(
        self, query: str, retrieved_docs: list[dict[str, Any]], top_k: int = 5
    ) -> str:
        """Analyze retrieval quality."""
        if not retrieved_docs:
            return json.dumps({"error": "No documents provided"})

        query_terms = set(query.lower().split())
        scores = []

        for doc in retrieved_docs:
            doc_terms = set(doc.get("text", "").lower().split())
            overlap = len(query_terms & doc_terms)
            recall = overlap / (len(query_terms) + 0.001)
            precision = overlap / (len(doc_terms) + 0.001)

            if recall + precision > 0:
                f1 = 2 * (recall * precision) / (recall + precision)
            else:
                f1 = 0

            scores.append(
                {
                    "doc_id": doc.get("id", doc.get("index", "unknown")),
                    "recall": round(recall, 3),
                    "precision": round(precision, 3),
                    "f1": round(f1, 3),
                }
            )

        scores.sort(key=lambda x: x["f1"], reverse=True)

        mr = 0
        for i, s in enumerate(scores[:top_k]):
            if s["f1"] > 0:
                mr += 1 / (i + 1)

        return json.dumps(
            {
                "query": query[:50],
                "docs_analyzed": len(retrieved_docs),
                "mrr": round(mr, 3),
                "scores": scores[:top_k],
            },
            indent=2,
        )

    async def tune_similarity(self, threshold: float = 0.7) -> str:
        """Show similarity threshold recommendations."""
        rec = {name: value for name, value in SIMILARITY_THRESHOLDS.items()}

        rec["recommended"] = threshold if threshold >= 0.7 else 0.7

        return json.dumps(
            {
                "thresholds": rec,
                "guidance": "Use 0.85+ for high-similarity tasks, 0.70 for general retrieval",
            },
            indent=2,
        )

    async def suggest_strategy(self, content_type: str) -> str:
        """Recommend chunk strategy for content type."""
        strategy = suggest_chunk_strategy(content_type)

        return json.dumps(
            {
                "content_type": content_type,
                "recommended": strategy,
                "alternatives": CHUNK_STRATEGIES,
            },
            indent=2,
        )

    async def rerank_results(self, query: str, results_json: str, top_k: int = 5) -> str:
        """Re-rank retrieval results."""
        try:
            results = json.loads(results_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON"})

        reranked = rerank_results(query, results, top_k)

        return json.dumps(
            {
                "query": query[:50],
                "original_count": len(results),
                "reranked_count": len(reranked),
                "results": reranked,
            },
            indent=2,
        )


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return SemanticRAGExtension(manifest, nexus_api)
