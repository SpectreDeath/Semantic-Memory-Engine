"""
SME logic layer: manifest lineage, reasoning distillation, and audit/drift analysis.
"""

from src.logic.audit_engine import AuditEngine
from src.logic.manifest_manager import ManifestManager
from src.logic.reasoning_quantizer import ReasoningQuantizer

__all__ = ["AuditEngine", "ManifestManager", "ReasoningQuantizer"]
