import hashlib
import hmac
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class HardwareSecurity:
    """
    Simulates a Hardware Security Module (HSM) or TPM (Trusted Platform Module).
    Used to anchor forensic evidence integrity with 'Hardware-Verified' signatures.
    """
    def __init__(self, secret_seed: str = "LAWNMOWER_SECURE_ENCLAVE_2026"):
        # Simulated hardware-fused private key
        self.key = hashlib.sha256(secret_seed.encode()).digest()
        self.device_id = "TPM_2.0_FS_MOCK"
        self.status = "HEALTHY"
        self.alerts = []
        self._integrity_vault = {} # Cache of verified hashes

    def sign_evidence(self, source_id: str, data_hash: str) -> str:
        """
        Creates a hardware-bound signature for a specific evidence hash.
        Simulates signing inside a secure enclave.
        """
        message = f"{source_id}:{data_hash}"
        signature = hmac.new(self.key, message.encode(), hashlib.sha256).hexdigest()
        return f"hws_v1_{signature[:16]}"

    def verify_integrity(self, source_id: str, data_hash: str, signature: str) -> bool:
        """
        Verifies if the data hash matches the hardware-bound signature.
        """
        if not signature:
            return False
        
        expected = self.sign_evidence(source_id, data_hash)
        is_valid = hmac.compare_digest(expected, signature)
        
        if not is_valid:
            self.trigger_tamper_alert(source_id)
            
        return is_valid

    def trigger_tamper_alert(self, source_id: str):
        """Logs a hardware-level tamper event."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "event": "TAMPER_DETECTED",
            "source": source_id,
            "severity": "CRITICAL"
        }
        self.alerts.append(alert)
        self.status = "ALERT_ACTIVE"

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns the hardware status and alert history."""
        return {
            "device_id": self.device_id,
            "status": self.status,
            "alert_count": len(self.alerts),
            "last_alerts": self.alerts[-5:],
            "enclave_timestamp": datetime.now().isoformat()
        }

# Global singleton for the gateway
_hsm = HardwareSecurity()

def get_hsm() -> HardwareSecurity:
    return _hsm
