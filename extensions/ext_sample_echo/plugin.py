import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("LawnmowerMan.ForensicEcho")

class ForensicEchoExtension:
    """
    Migrated Forensic Echo Extension (v1.1.1).
    Standard Boilerplate for Lawnmower Man Extensions.
    """
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id", "ext_sample_echo")

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Forensic Echo activation sequence complete.")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        # Echo logic: Just log the ingestion
        logger.debug(f"[{self.plugin_id}] Ingestion event detected: {len(raw_data)} chars.")
        return {"plugin": self.plugin_id, "status": "processed"}

    def get_tools(self) -> list:
        return [self.echo_forensic_metadata]

    async def echo_forensic_metadata(self, file_path: str) -> str:
        """
        Extract file metadata and sign it with the TPM enclave.
        """
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found: {file_path}"})
        
        stats = os.stat(file_path)
        metadata = {
            "file_path": os.path.abspath(file_path),
            "size_bytes": stats.st_size,
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "plugin": "Forensic Echo v1.1.1"
        }
        
        # Access the TPM via the Nexus API (SmeCoreBridge)
        # SmeCoreBridge doesn't directly expose get_hsm(), but mcp_server.py imports it.
        # Actually, in mcp_server.py, we pass sme_core as nexus_api.
        # SmeCoreBridge has access to get_nexus(), but not directly HSM.
        # However, the user's template implies nexus_api contains TPM access.
        # I should probably update SmeCoreBridge to expose HSM or pass HSM separately.
        
        # For now, let's use the gateway's hardware_security directly as before, 
        # or assume nexus_api has a way to get it.
        from gateway.hardware_security import get_hsm
        hsm = get_hsm()
        
        data_hash = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
        signature = hsm.sign_evidence("ForensicEcho", data_hash)
        
        metadata["hw_signature"] = signature
        metadata["integrity_status"] = "Hardware-Signed"
        
        return json.dumps(metadata, indent=2)

def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    return ForensicEchoExtension(manifest, nexus_api)
