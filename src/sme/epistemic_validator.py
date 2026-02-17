import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from gateway.hardware_security import get_hsm

logger = logging.getLogger("SME.Epistemic")

class DataNode:
    """
    High-performance data structure for file metadata.
    Uses __slots__ to minimize RAM overhead during recursive audits.
    """
    __slots__ = [
        'file', 'path', 'entropy', 'burstiness', 
        'vault_proximity', 'nts', 'verdict', 
        'attribution', 'sda_warning'
    ]

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot))

    def to_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}

class EpistemicValidator:
    """
    Evaluates forensic claims based on Epistemic Reliabilism and source provenance.
    Optimized with __slots__ for memory efficiency during large audits.
    """
    __slots__ = ['core', 'category']

    def __init__(self, core_bridge):
        self.core = core_bridge
        self.category = 'forensics'

    def evaluate_claim(self, claim: str, evidence_sources: list):
        """
        Assigns an 'Epistemic Certainty Score' (CQ) based on source provenance.
        Includes 'Hardware-Verified' integrity checks using the HSM.
        """
        hsm = get_hsm()
        score = 0.0
        justifications = []
        hardware_verified = True

        for source in evidence_sources:
            s_id = source.get('id', 'Unknown')
            # Query the core for reliability metadata
            provenance = self.core.get_source_reliability(s_id)
            tier = provenance.get("tier", 1)  # 1 (Low) to 5 (High)
            
            # Hardware Integrity Check (Sprint 11)
            hw_sig = source.get("hw_signature")
            db_hash = provenance.get("hash")
            
            if db_hash and hw_sig:
                if hsm.verify_integrity(s_id, db_hash, hw_sig):
                    justifications.append(f"Source '{s_id}': Hardware Integrity Verified (TPM).")
                else:
                    justifications.append(f"CRITICAL: Source '{s_id}' TAMPER ALERT! Signature mismatch.")
                    hardware_verified = False
                    tier = 0 # invalidate the source
            elif db_hash:
                 justifications.append(f"Source '{s_id}': No Hardware Signature found. Relying on soft hash.")
            
            trust = tier / 5.0
            score += trust
            tamper_info = " [Tamper-Evident]" if provenance.get("tamper_evident") else ""
            justifications.append(f"Source '{s_id}' provides Tier-{tier} grounding (Trust: {trust}){tamper_info}.")

        # Normalize score between 0.0 and 1.0
        cq = min(score, 1.0)
        
        # Severe penalty for any hardware tamper
        if not hardware_verified:
            cq *= 0.1
            status = "Rejected (TAMPER DETECTED)"
        else:
            if cq >= 0.7:
                status = "Verified"
            elif cq >= 0.4:
                status = "Speculative"
            else:
                status = "Rejected"

        return {
            "claim": claim,
            "certainty_quotient": round(cq, 4),
            "status": status,
            "hardware_verified": hardware_verified,
            "audit_trail": justifications,
            "epistemic_stance": "Hardware-Anchored Reliabilism",
            "timestamp": datetime.now().isoformat()
        }
