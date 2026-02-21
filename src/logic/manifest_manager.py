import hashlib
import json
import os
from datetime import datetime

class ManifestManager:
    def __init__(self, manifest_path: str = None):
        if manifest_path is None:
            self.path = os.getenv("MANIFEST_PATH", "data/manifest.json")
        else:
            self.path = manifest_path
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return json.load(f)
        return {"sources": {}, "last_updated": None}

    def get_file_hash(self, filepath):
        """Generates a hash. For 10GB files, we only hash the first/last MB for speed."""
        hash_md5 = hashlib.md5()
        size = os.path.getsize(filepath)
        with open(filepath, "rb") as f:
            if size > 10_000_000: # If > 10MB, use 'Forensic Sampling'
                hash_md5.update(f.read(1024 * 1024)) # First MB
                f.seek(-1024 * 1024, os.SEEK_END)
                hash_md5.update(f.read(1024 * 1024)) # Last MB
            else:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        return f"{hash_md5.hexdigest()}_{size}"

    def is_stale(self, filepath):
        if not os.path.exists(filepath):
            return False
        current_hash = self.get_file_hash(filepath)
        stored_hash = self.data["sources"].get(filepath, {}).get("hash")
        return current_hash != stored_hash

    def update_source(self, filepath):
        self.data["sources"][filepath] = {
            "hash": self.get_file_hash(filepath),
            "timestamp": datetime.now().isoformat()
        }
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=4)