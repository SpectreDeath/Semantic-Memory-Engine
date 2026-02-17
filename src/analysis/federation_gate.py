"""
🛰️ Federation Gate v2.2.5 — Anonymity Middleware

Ensures that any data intended for the Federated Vector Store 
or external export is aggressively redacted.
"""

import logging
from src.core.redactor import Redactor

logger = logging.getLogger(__name__)

class FederationGate:
    """
    Final security layer before data leaves the local node.
    Enforces Strict Redaction Mode to prevent PII leakage.
    """

    @staticmethod
    def prepare_for_federation(content: str) -> str:
        """
        Hardens content for shared memory by applying strict redaction.
        
        Args:
            content: The forensic data or rhetorical signature text.
        
        Returns:
            Strictly sanitized content.
        """
        if not content:
            return ""

        logger.info("Federation Gate: Applying strict anonymity pass.")
        
        # Apply strict redaction (scrapes IDs, phones, IPs, and identifies common name leaks)
        hardened = Redactor.redact(content, strict=True)
        
        return hardened

    @staticmethod
    def audit_signature(signature_data: dict) -> dict:
        """
        Audits a full signature object for PII before export.
        Redacts any string fields.
        """
        for key, value in signature_data.items():
            if isinstance(value, str):
                signature_data[key] = Redactor.redact(value, strict=True)
        return signature_data
