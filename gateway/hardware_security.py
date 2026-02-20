import hashlib
import hmac
import os
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class HardwareSecurity:
    """
    Simulates a Hardware Security Module (HSM) or TPM (Trusted Platform Module).
    Used to anchor forensic evidence integrity with 'Hardware-Verified' signatures.

    The signing seed is loaded from the SME_HSM_SECRET environment variable.
    If the variable is absent a placeholder is used and a CRITICAL warning is logged.
    """

    def __init__(self):
        raw_seed = os.environ.get("SME_HSM_SECRET")
        if not raw_seed:
            logger.critical(
                "SME_HSM_SECRET is not set. The HSM is using an insecure placeholder "
                "seed — evidence signatures can be trivially forged. "
                "Set the SME_HSM_SECRET environment variable."
            )
            raw_seed = "INSECURE-PLACEHOLDER-SET-SME_HSM_SECRET"

        # Simulated hardware-fused private key derived from the seed
        self.key = hashlib.sha256(raw_seed.encode()).digest()
        self.device_id = "TPM_2.0_FS_MOCK"
        self.status = "HEALTHY"
        self.alerts: List[Dict[str, Any]] = []
        self._integrity_vault: Dict[str, str] = {}

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
            "severity": "CRITICAL",
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
            "enclave_timestamp": datetime.now().isoformat(),
        }


# Thread-safe global singleton
_hsm: Optional[HardwareSecurity] = None
_hsm_lock = threading.Lock()


def get_hsm() -> HardwareSecurity:
    global _hsm
    with _hsm_lock:
        if _hsm is None:
            _hsm = HardwareSecurity()
    return _hsm
