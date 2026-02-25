from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable

class PluginDAL:
    """
    Data Access Layer (DAL) for plugins.
    Provides standard database operations without tying plugins to specific SQL dialects.
    """
    def __init__(self, nexus_api: Any):
        self.nexus_api = nexus_api

    def create_table(self, table_name: str, schema: Dict[str, str]) -> None:
        """
        Creates a table given a simple schema.
        Translates types generically (e.g. PRIMARY_KEY, STRING, FLOAT, BOOLEAN, TEXT, DATETIME)
        """
        # simplified generation for standard types
        columns = []
        for col_name, col_type in schema.items():
            if col_type == "PRIMARY_KEY":
                columns.append(f"{col_name} INTEGER PRIMARY KEY AUTOINCREMENT")  # Will be adjusted for postgres later
            elif col_type in ("STRING", "TEXT"):
                columns.append(f"{col_name} TEXT")
            elif col_type == "FLOAT":
                columns.append(f"{col_name} REAL")
            elif col_type == "BOOLEAN":
                columns.append(f"{col_name} BOOLEAN")
            elif col_type == "DATETIME":
                columns.append(f"{col_name} TEXT")
            else:
                columns.append(f"{col_name} {col_type}")
                
        cols_str = ", ".join(columns)
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols_str})"
        self.nexus_api.nexus.execute(sql)

    def insert_record(self, table_name: str, data: Dict[str, Any]) -> None:
        """Inserts a record into the table."""
        cols = list(data.keys())
        placeholders = ", ".join(["?" for _ in cols])
        cols_str = ", ".join(cols)
        sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
        self.nexus_api.nexus.execute(sql, tuple(data.values()))

    def get_count(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> int:
        """Returns the count of rows matching conditions."""
        sql = f"SELECT COUNT(*) as cnt FROM {table_name}"
        params = []
        if conditions:
            conds = []
            for k, v in conditions.items():
                conds.append(f"{k} = ?")
                params.append(v)
            sql += " WHERE " + " AND ".join(conds)
            
        result = self.nexus_api.nexus.query(sql, tuple(params))
        return result[0]["cnt"] if result else 0
        
    def get_recent(self, table_name: str, columns: List[str], order_by: str, limit: int = 10) -> List[Dict]:
        """Gets recent records."""
        cols_str = ", ".join(columns) if columns else "*"
        sql = f"SELECT {cols_str} FROM {table_name} ORDER BY {order_by} DESC LIMIT ?"
        return self.nexus_api.nexus.query(sql, (limit,))


class BasePlugin(ABC):
    """
    Abstract Base Class for all Semantic Memory Engine (SME) extensions/plugins.
    Enforces a standard lifecycle and tool exposure contract.
    """

    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        """
        Initialize the plugin with its manifest configuration and the Nexus API.
        
        Args:
            manifest (Dict[str, Any]): The configuration parsed from the plugin's manifest.json.
            nexus_api (Any): Standard interface (SmeCoreBridge or similar) to the database/core engine.
        """
        self.manifest = manifest
        self.nexus = nexus_api
        self.dal = PluginDAL(nexus_api)
        self.plugin_id = manifest.get("plugin_id", self.__class__.__name__)

    async def on_startup(self) -> None:
        """
        Lifecycle hook executed when the plugin is first loaded.
        Default implementation is a no-op.
        """
        pass

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lifecycle hook executed when new data is ingested into the system.
        Default implementation returns a 'skipped' status.
        """
        return {"status": "skipped", "reason": "No ingestion handler implemented."}

    async def on_event(self, event_id: str, payload: Dict[str, Any]) -> None:
        """
        V3.0 Event Bus Hook: Responds to system-wide events.
        Default implementation does nothing (override in subclasses).
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[Callable[..., Any]]:
        """
        Declares the functions this plugin exposes to the AI Agent (e.g., via MCP).
        """
        pass
