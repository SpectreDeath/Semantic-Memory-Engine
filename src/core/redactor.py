import re
import logging
from typing import List, Pattern

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REDACTION_MARKER = "[REDACTED]"

# ---------------------------------------------------------------------------
# Core Redactor Patterns (v2.2.5)
# ---------------------------------------------------------------------------

# Proper names: 2+ consecutive capitalized words
# Excludes single capitalized words at start of sentence
_PATTERN_PROPER_NAME = re.compile(
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
)

# Email addresses
_PATTERN_EMAIL = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# URLs (http/https/ftp)
_PATTERN_URL = re.compile(
    r'https?://[^\s\)\]>\"\']+|ftp://[^\s\)\]>\"\']+',
    re.IGNORECASE,
)

# Phone numbers (Global/US/Local heuristics)
# Catches: 555-1212, (555) 555-1212, +1 555-555-1212
_PATTERN_PHONE = re.compile(
    r'(\+?\d{1,3}[-. ]?)?\(?(\d{3})\)?[-. ]?(\d{3})[-. ]?(\d{4})\b|' # 10-digit
    r'\b\d{3}[-. ]\d{4}\b'                                         # 7-digit
)

# IP Addresses (IPv4 and IPv6)
_PATTERN_IP = re.compile(
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b|'             # IPv4
    r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b'  # IPv6
)

# Strict Mode patterns (more aggressive, handles possible ID leaks)
_PATTERN_STRICT_ID = re.compile(
    r'\b\d{3}-\d{2}-\d{4}\b|'                 # SSN (simplistic)
    r'\b[A-Z]{1,2}\d{6,9}\b',                 # Passport-like patterns
    re.IGNORECASE
)

# Technical false positives to preserve in strict mode (optionally)
# e.g., "Python Version", "Windows Data"
_TECHNICAL_PRESERVE = [
    "Python", "Windows", "Linux", "Forensic", "Artifact",
    "SME", "Laboratory", "Analyst", "Subject", "Evidence"
]

class Redactor:
    """
    Centralized PII and Entity Redaction engine for federation safety.
    
    Hardens data anonymity for SME v3.0.0 by stripping identifying 
    metadata via regex heuristics.
    """

    @classmethod
    def redact(cls, text: str, strict: bool = False) -> str:
        """
        Sanitize text by replacing PII with [REDACTED].
        
        Args:
            text: The raw source material.
            strict: If True, applies more aggressive scrubbing for 
                    federated vector storage.
        
        Returns:
            Sanitized text.
        """
        if not text:
            return ""

        # Tier 1: Digital Footprints (URLs, IPs, Emails)
        redacted = _PATTERN_URL.sub(REDACTION_MARKER, text)
        redacted = _PATTERN_IP.sub(REDACTION_MARKER, redacted)
        redacted = _PATTERN_EMAIL.sub(REDACTION_MARKER, redacted)

        # Tier 2: Personal Metadata (Phones, Proper Names)
        redacted = _PATTERN_PHONE.sub(REDACTION_MARKER, redacted)
        
        if strict:
            # Aggressive ID scrubbing
            redacted = _PATTERN_STRICT_ID.sub(REDACTION_MARKER, redacted)
            
            # Name scrubbing with technical preservation
            # We don't want to redact common technical terms that look like names
            redacted = cls._smart_name_redact(redacted)
        else:
            redacted = _PATTERN_PROPER_NAME.sub(REDACTION_MARKER, redacted)

        return redacted

    @classmethod
    def _smart_name_redact(cls, text: str) -> str:
        """
        Redacts names while trying to preserve common technical terminology.
        """
        def replace_func(match):
            name = match.group(1)
            # If any part of the name is in our preserve list, keep it
            words = name.split()
            if any(w in _TECHNICAL_PRESERVE for w in words):
                return name
            return REDACTION_MARKER

        return _PATTERN_PROPER_NAME.sub(replace_func, text)
