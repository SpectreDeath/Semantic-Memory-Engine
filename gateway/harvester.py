import os
import re
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("lawnmower.harvester")

class EvidenceHarvester:
    """
    Proactive evidence collection and linguistic fingerprinting engine.
    """
    def __init__(self):
        # Regex for forensic redaction
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[0-Z|a-z]{2,}\b')
        # Tech jargon: simple common technical tokens that might bias style
        self.jargon_pattern = re.compile(r'\b(api|json|xml|http|https|cli|sdk|mcp|sme|stylometry|forensics|git|commit|push|pull)\b', re.IGNORECASE)

    def clean_text(self, text: str) -> str:
        """ Forensic Redaction: Removes identifiers and tech jargon. """
        text = self.url_pattern.sub("[URL]", text)
        text = self.email_pattern.sub("[EMAIL]", text)
        text = self.jargon_pattern.sub("[JARGON]", text)
        return text

    def walk_directory(self, root_path: str) -> str:
        """ Recursively harvests text from supported files. """
        combined_text = []
        supported_exts = {'.txt', '.log', '.md'}
        
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Path not found: {root_path}")

        for root, dirs, files in os.walk(root_path):
            for file in files:
                if any(file.endswith(ext) for ext in supported_exts):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            combined_text.append(content)
                    except Exception as e:
                        logger.warning(f"Harvester: Failed to read {file_path}: {e}")
        
        return "\n\n".join(combined_text)

    def generate_stylometric_fingerprint(self, text: str) -> Dict[str, Any]:
        """
        Creates a basic token frequency profile compatible with Scribe Pro.
        In a production SME system, this would use NLTK or spacy.
        """
        cleaned = self.clean_text(text)
        # Simplified tokenization for the simulation
        tokens = re.findall(r'\b\w+\b', cleaned.lower())
        
        total = len(tokens)
        if total == 0:
            return {"tokens": {}, "total": 0}

        counts = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        
        # Relative frequency for normalization
        fingerprint = {
            "token_counts": counts,
            "total_tokens": total,
            "vocabulary_size": len(counts),
            "top_tokens": sorted(counts.items(), key=lambda x: x[1], reverse=True)[:50]
        }
        return fingerprint

    def harvest(self, path: str) -> Dict[str, Any]:
        """ Main entry point for harvesting a path. """
        logger.info(f"Harvester: Starting scan of {path}")
        raw_text = self.walk_directory(path)
        fingerprint = self.generate_stylometric_fingerprint(raw_text)
        logger.info(f"Harvester: Scan complete. {fingerprint['total_tokens']} tokens harvested.")
        return fingerprint
