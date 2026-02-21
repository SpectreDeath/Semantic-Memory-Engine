"""
SME logic layer: manifest lineage, reasoning distillation, and audit/drift analysis.
"""

from src.logic.manifest_manager import ManifestManager
from src.logic.reasoning_quantizer import ReasoningQuantizer
from src.logic.audit_engine import AuditEngine

__all__ = ["ManifestManager", "ReasoningQuantizer", "AuditEngine"]
