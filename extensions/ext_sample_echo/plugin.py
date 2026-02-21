import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports
from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.ForensicEcho")

class ForensicEchoExtension(BasePlugin):
    """
    Migrated Forensic Echo Extension (v1.1.1).
    Standard Boilerplate for Lawnmower Man Extensions.
    """
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)

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
        
        # NexusAPI: use nexus_api.get_hsm() — no gateway imports
        hsm = self.nexus.get_hsm()
        
        data_hash = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
        signature = hsm.sign_evidence("ForensicEcho", data_hash)
        
        metadata["hw_signature"] = signature
        metadata["integrity_status"] = "Hardware-Signed"
        
        return json.dumps(metadata, indent=2)

def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    return ForensicEchoExtension(manifest, nexus_api)
