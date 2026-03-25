import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.DataStorage")

try:
    from src.core.semantic_db import SemanticDatabase
except ImportError:
    SemanticDatabase = None

try:
    from src.core.centrifuge import CentrifugeStorage
except ImportError:
    CentrifugeStorage = None

try:
    from src.core.data_manager import DataManager
except ImportError:
    DataManager = None


class DataStorageExtension(BasePlugin):
    """
    Data Storage Extension for SME.
    Provides semantic database, centrifuge storage, and data management.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.semantic_db = SemanticDatabase() if SemanticDatabase else None
        self.centrifuge = CentrifugeStorage() if CentrifugeStorage else None
        self.data_manager = DataManager() if DataManager else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Data Storage extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.store_semantic,
            self.query_semantic,
            self.centrifuge_store,
            self.centrifuge_retrieve,
            self.manage_data,
            self.backup_data,
        ]

    async def store_semantic(self, key: str, value: Any, metadata: dict = None) -> str:
        """Store data in semantic database."""
        if not self.semantic_db:
            return json.dumps({"error": "SemanticDatabase not available"})
        try:
            result = self.semantic_db.store(key, value, metadata)
            return json.dumps({"status": "stored", "key": key})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def query_semantic(self, query: str, filters: dict = None, limit: int = 10) -> str:
        """Query semantic database."""
        if not self.semantic_db:
            return json.dumps({"error": "SemanticDatabase not available"})
        try:
            results = self.semantic_db.query(query, filters, limit)
            return json.dumps({"query": query, "count": len(results), "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def centrifuge_store(self, data: Any, tier: str = "hot") -> str:
        """Store data in centrifuge high-performance storage."""
        if not self.centrifuge:
            return json.dumps({"error": "CentrifugeStorage not available"})
        try:
            result = self.centrifuge.store(data, tier)
            return json.dumps({"status": "stored", "tier": tier})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def centrifuge_retrieve(self, key: str) -> str:
        """Retrieve data from centrifuge storage."""
        if not self.centrifuge:
            return json.dumps({"error": "CentrifugeStorage not available"})
        try:
            data = self.centrifuge.retrieve(key)
            return json.dumps({"key": key, "data": data})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def manage_data(self, operation: str, collection: str, data: Any = None) -> str:
        """Manage data collections (CRUD operations)."""
        if not self.data_manager:
            return json.dumps({"error": "DataManager not available"})
        try:
            result = self.data_manager.manage(operation, collection, data)
            return json.dumps({"operation": operation, "collection": collection, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def backup_data(self, target_path: str, collections: list[str] = None) -> str:
        """Backup data collections to specified path."""
        if not self.data_manager:
            return json.dumps({"error": "DataManager not available"})
        try:
            result = self.data_manager.backup(target_path, collections)
            return json.dumps({"status": "backed_up", "target": target_path})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return DataStorageExtension(manifest, nexus_api)
