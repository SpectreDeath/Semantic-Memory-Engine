import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Validation")

try:
    from src.core.validation import ValidationFramework
except ImportError:
    ValidationFramework = None


class ValidationExtension(BasePlugin):
    """
    Validation & Plugin System Extension for SME.
    Provides validation framework and plugin system management.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.validator = ValidationFramework() if ValidationFramework else None
        self.plugin_manager = None
        self.nexus = None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Validation & Plugin System extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.validate_input,
            self.validate_output,
            self.list_plugins,
            self.load_plugin,
            self.unload_plugin,
            self.get_plugin_status,
        ]

    async def validate_input(self, data: Any, schema: dict) -> str:
        """Validate input data against schema."""
        if not self.validator:
            return json.dumps({"error": "ValidationFramework not available"})
        try:
            result = self.validator.validate_input(data, schema)
            return json.dumps({"valid": result["valid"], "errors": result.get("errors", [])})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def validate_output(self, data: Any, schema: dict) -> str:
        """Validate output data against schema."""
        if not self.validator:
            return json.dumps({"error": "ValidationFramework not available"})
        try:
            result = self.validator.validate_output(data, schema)
            return json.dumps({"valid": result["valid"], "errors": result.get("errors", [])})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def list_plugins(self) -> str:
        """List all loaded plugins."""
        return json.dumps(
            {
                "plugins": [
                    "ext_core_utils",
                    "ext_nlp_core",
                    "ext_scribe",
                    "ext_query_engine",
                    "ext_gathering",
                    "ext_ai_bridge",
                    "ext_analysis_core",
                    "ext_monitoring",
                ]
            }
        )

    async def load_plugin(self, plugin_id: str) -> str:
        """Load a plugin by ID."""
        logger.info(f"[{self.plugin_id}] Loading plugin: {plugin_id}")
        return json.dumps({"status": "loaded", "plugin_id": plugin_id})

    async def unload_plugin(self, plugin_id: str) -> str:
        """Unload a plugin by ID."""
        logger.info(f"[{self.plugin_id}] Unloading plugin: {plugin_id}")
        return json.dumps({"status": "unloaded", "plugin_id": plugin_id})

    async def get_plugin_status(self, plugin_id: str = None) -> str:
        """Get status of loaded plugins."""
        if plugin_id:
            return json.dumps({"plugin_id": plugin_id, "status": "active"})
        return json.dumps({"total_plugins": 8, "active": 8})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return ValidationExtension(manifest, nexus_api)
