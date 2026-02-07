"""
SME Forensic Utilities Package

Provides tools for data auditing, project context sniffing, 
and Gephi visualization streaming.
"""

from src.utils.auditor import detect_outliers, load_data as load_audit_data
from src.utils.context_sniffer import get_ext, scan_keywords, get_persona, update_json as update_persona
from src.utils.gephi_bridge import (
    connect_to_gephi, 
    stream_project_mode, 
    stream_trust_mode, 
    stream_knowledge_mode, 
    stream_synthetic_mode
)

__all__ = [
    "detect_outliers",
    "load_audit_data",
    "get_ext",
    "scan_keywords",
    "get_persona",
    "update_persona",
    "connect_to_gephi",
    "stream_project_mode",
    "stream_trust_mode",
    "stream_knowledge_mode",
    "stream_synthetic_mode",
]
