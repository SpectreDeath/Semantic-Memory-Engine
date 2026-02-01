import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("lawnmower.nexus")

class ForensicNexus:
    """
    Unified database layer using SQLite ATTACH.
    Provides a single entry point for all forensic data across laboratory,
    provenance, and analytics databases.
    """
    def __init__(self, base_dir: str = "d:/SME/data"):
        self.base_dir = base_dir
        self.primary_path = os.path.normpath(os.path.join(base_dir, "forensic_nexus.db"))
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.primary_path), exist_ok=True)
        
        # Connect to master DB
        self.conn = sqlite3.connect(self.primary_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Attach subordinate databases
        self._attach_subordinates()
        
    def _attach_subordinates(self):
        databases = {
            "lab": os.path.normpath(os.path.join(self.base_dir, "storage", "laboratory.db")),
            "prov": os.path.normpath(os.path.join(self.base_dir, "provenance.db")),
            "core": os.path.normpath(os.path.join(self.base_dir, "knowledge_core.sqlite"))
        }
        
        # Ensure lab dir exists or ATTACH will fail if path doesn't exist at all
        os.makedirs(os.path.join(self.base_dir, "storage"), exist_ok=True)
        
        for schema, path in databases.items():
            abs_path = os.path.abspath(path)
            # SQLite ATTACH works even if file doesn't exist (it creates it), 
            # but we want to know if we are attaching existing data.
            try:
                # Use a separate connector to ensure the file exists so ATTACH doesn't fail on missing dirs
                if not os.path.exists(abs_path):
                    with sqlite3.connect(abs_path) as tmp:
                        pass
                
                # Check if already attached
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA database_list")
                attached = [row[1] for row in cursor.fetchall()]
                
                if schema not in attached:
                    self.conn.execute(f"ATTACH DATABASE '{abs_path}' AS {schema}")
                    logger.info(f"Nexus: Attached {schema} from {abs_path}")
            except Exception as e:
                logger.warning(f"Nexus: Failed to attach {schema} ({abs_path}): {e}")

    def attach_db(self, db_path: str, schema_name: str):
        """Dynamically attach a new database to the nexus."""
        abs_path = os.path.normpath(os.path.abspath(db_path))
        if not os.path.exists(abs_path):
            # Ensure file exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with sqlite3.connect(abs_path) as tmp:
                pass
        
        try:
            # Check if schema_name is valid (alphanumeric or underscore)
            if not all(c.isalnum() or c == '_' for c in schema_name):
                raise ValueError(f"Invalid schema name: {schema_name}")
                
            self.conn.execute(f"ATTACH DATABASE '{abs_path}' AS {schema_name}")
            logger.info(f"Nexus: Dynamically attached {schema_name} from {abs_path}")
        except Exception as e:
            if "already in use" in str(e):
                return # Already attached
            logger.error(f"Nexus Attach Error: {e}")
            raise

    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Run a cross-database query and return results as dicts."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Nexus Query Error: {e}\nSQL: {sql}")
            return []

    def execute(self, sql: str, params: tuple = ()):
        """Execute a write operation."""
        try:
            self.conn.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Nexus Execution Error: {e}\nSQL: {sql}")
            self.conn.rollback()
            raise

    def get_unified_forensic_feed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Cross-DB JOIN example: Link forensic events to their source reliability.
        """
        sql = """
            SELECT 
                e.timestamp, 
                e.tool_name, 
                e.event_type, 
                e.target, 
                e.confidence,
                p.reliability_tier,
                p.acquisition_method
            FROM lab.forensic_events e
            LEFT JOIN prov.source_provenance p ON e.target = p.source_id
            ORDER BY e.timestamp DESC
            LIMIT ?
        """
        return self.query(sql, (limit,))

    def get_status(self) -> Dict[str, Any]:
        """Return the status of attached databases."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA database_list")
        return {
            "primary": self.primary_path,
            "attached": [dict(row) for row in cursor.fetchall()]
        }

# Global Nexus instance
_nexus = None

def get_nexus(base_dir: str = "d:/SME/data") -> ForensicNexus:
    global _nexus
    if _nexus is None:
        _nexus = ForensicNexus(base_dir)
    return _nexus
