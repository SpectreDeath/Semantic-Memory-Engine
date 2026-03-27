"""
SME Forensic Utilities Package

Provides tools for data auditing, project context sniffing,
and Gephi visualization streaming.
"""

from src.utils.auditor import detect_outliers
from src.utils.auditor import load_data as load_audit_data
from src.utils.context_sniffer import get_ext, get_persona, scan_keywords
from src.utils.context_sniffer import update_json as update_persona
from src.utils.gephi_bridge import (
    connect_to_gephi,
    stream_knowledge_mode,
    stream_project_mode,
    stream_synthetic_mode,
    stream_trust_mode,
)

__all__ = [
    "connect_to_gephi",
    "detect_outliers",
    "get_ext",
    "get_persona",
    "load_audit_data",
    "scan_keywords",
    "stream_knowledge_mode",
    "stream_project_mode",
    "stream_synthetic_mode",
    "stream_trust_mode",
    "update_persona",
]
