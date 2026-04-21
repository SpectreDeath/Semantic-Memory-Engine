import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.APIKeyManager")

KEYS_DIR = Path(__file__).parent / "keys"
KEYS_FILE = KEYS_DIR / "encrypted_keys.json"
MASTER_KEY_FILE = KEYS_DIR / ".master.key"


class APIKeyManager:
    def __init__(self):
        self._fernet = self._get_fernet()
        self.keys: dict[str, dict[str, Any]] = {}
        self._load_keys()

    def _get_fernet(self):
        KEYS_DIR.mkdir(parents=True, exist_ok=True)
        if MASTER_KEY_FILE.exists():
            with open(MASTER_KEY_FILE, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(MASTER_KEY_FILE, "wb") as f:
                f.write(key)
        return Fernet(key)

    def _load_keys(self):
        if KEYS_FILE.exists():
            try:
                with open(KEYS_FILE) as f:
                    self.keys = json.load(f)
                logger.info(f"Loaded {len(self.keys)} API keys")
            except Exception as e:
                logger.exception(f"Failed to load API keys: {e}")
                self.keys = {}

    def _save_keys(self):
        with open(KEYS_FILE, "w") as f:
            json.dump(self.keys, f, indent=2)

    def add_key(
        self,
        name: str,
        api_key: str,
        provider: str,
        expiry_days: int | None = None,
        notes: str = "",
    ) -> str:
        key_id = f"key_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        encrypted = self._fernet.encrypt(api_key.encode()).decode()

        expiry = None
        if expiry_days:
            expiry = (datetime.now() + timedelta(days=expiry_days)).isoformat()

        self.keys[key_id] = {
            "id": key_id,
            "name": name,
            "provider": provider,
            "encrypted_key": encrypted,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
            "expiry": expiry,
            "last_used": None,
            "rotation_reminder_sent": False,
        }
        self._save_keys()
        logger.info(f"Added API key: {name} ({provider})")
        return key_id

    def get_key(self, key_id: str) -> str | None:
        if key_id not in self.keys:
            return None
        encrypted = self.keys[key_id]["encrypted_key"]
        decrypted = self._fernet.decrypt(encrypted.encode()).decode()
        self.keys[key_id]["last_used"] = datetime.now().isoformat()
        self._save_keys()
        return decrypted

    def list_keys(self, include_values: bool = False) -> list[dict[str, Any]]:
        result = []
        for key in self.keys.values():
            key_copy = dict(key)
            if not include_values:
                key_copy.pop("encrypted_key", None)
            else:
                key_copy["value"] = self.get_key(key_copy["id"])
            result.append(key_copy)
        return result

    def update_key(self, key_id: str, name: str | None = None, notes: str | None = None) -> bool:
        if key_id not in self.keys:
            return False
        if name:
            self.keys[key_id]["name"] = name
        if notes:
            self.keys[key_id]["notes"] = notes
        self._save_keys()
        return True

    def delete_key(self, key_id: str) -> bool:
        if key_id in self.keys:
            del self.keys[key_id]
            self._save_keys()
            logger.info(f"Deleted API key: {key_id}")
            return True
        return False

    def get_expiring_keys(self, days: int = 7) -> list[dict[str, Any]]:
        expiring = []
        for key in self.keys.values():
            if key.get("expiry"):
                expiry_date = datetime.fromisoformat(key["expiry"])
                if expiry_date <= datetime.now() + timedelta(days=days):
                    expiring.append(key)
        return expiring


class APIKeyManagerExtension(BasePlugin):
    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.manager = APIKeyManager()

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] API Key Manager extension activated")
        expiring = self.manager.get_expiring_keys()
        if expiring:
            logger.warning(f"{len(expiring)} API keys expiring soon")

    def get_tools(self):
        return [
            self.add_api_key,
            self.get_api_key,
            self.list_api_keys,
            self.update_api_key,
            self.delete_api_key,
            self.get_expiring_keys,
        ]

    async def add_api_key(
        self,
        name: str,
        api_key: str,
        provider: str,
        expiry_days: int = 0,
        notes: str = "",
    ) -> str:
        """Add a new API key."""
        expiry = expiry_days if expiry_days > 0 else None
        key_id = self.manager.add_key(name, api_key, provider, expiry, notes)
        return json.dumps({"key_id": key_id, "status": "added"})

    async def get_api_key(self, key_id: str) -> str:
        """Retrieve an API key (returns decrypted value)."""
        key = self.manager.get_key(key_id)
        if key:
            return json.dumps({"key_id": key_id, "api_key": key})
        return json.dumps({"error": "Key not found"})

    async def list_api_keys(self, include_values: bool = False) -> str:
        """List all API keys."""
        return json.dumps({"keys": self.manager.list_keys(include_values)})

    async def update_api_key(self, key_id: str, name: str = "", notes: str = "") -> str:
        """Update API key metadata."""
        success = self.manager.update_key(key_id, name or None, notes or None)
        return json.dumps({"key_id": key_id, "status": "updated" if success else "not_found"})

    async def delete_api_key(self, key_id: str) -> str:
        """Delete an API key."""
        success = self.manager.delete_key(key_id)
        return json.dumps({"key_id": key_id, "status": "deleted" if success else "not_found"})

    async def get_expiring_keys(self, days: int = 7) -> str:
        """Get API keys expiring within specified days."""
        return json.dumps({"expiring": self.manager.get_expiring_keys(days)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return APIKeyManagerExtension(manifest, nexus_api)
