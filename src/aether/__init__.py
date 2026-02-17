"""
The Aether: Federated Semantic Memory Layer

Phase 3 Implementation:
- Vector Syncing: Hybrid Local/Supabase vector store with prioritized caching
- Collaborative Forensic Profiles: Secure hashed signature sharing between SME nodes
- Self-Correcting Epistemic Gates: SLM-based recursive trust validation

Technical Targets:
- VRAM Floor: 4GB
- Processing Latency: <1s for rhetorical signature extraction
- Scalability: 1M+ signatures using Polars native IPC
"""

from .vector_syncer import VectorSyncer, VectorStoreType
from .signature_library import SignatureLibrary, SignatureNode
from .epistemic_gate import EpistemicGate, GateDecision

__all__ = [
    "VectorSyncer",
    "VectorStoreType", 
    "SignatureLibrary",
    "SignatureNode",
    "EpistemicGate",
    "GateDecision",
]
