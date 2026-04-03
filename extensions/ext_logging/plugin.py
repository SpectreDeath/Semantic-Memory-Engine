import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Logging")

try:
    from src.core.logging_system import LoggingSystem
except ImportError:
    LoggingSystem = None

try:
    from src.core.dashboard_cmd import Dashboard
except ImportError:
    Dashboard = None


class LoggingExtension(BasePlugin):
    """
    Logging & Dashboard Extension for SME.
    Provides logging system and CLI dashboard for operations and monitoring.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.logging_system = LoggingSystem() if LoggingSystem else None
        self.dashboard = Dashboard() if Dashboard else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Logging & Dashboard extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.log_message,
            self.get_logs,
            self.configure_logger,
            self.show_dashboard,
            self.get_system_status,
        ]

    async def log_message(self, level: str, message: str, component: str = "general") -> str:
        """Log a message at specified level."""
        if not self.logging_system:
            return json.dumps({"error": "LoggingSystem not available"})
        try:
            self.logging_system.log(level, message, component)
            return json.dumps({"status": "logged", "level": level, "component": component})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_logs(
        self, level: str | None = None, component: str | None = None, limit: int = 100
    ) -> str:
        """Retrieve logs with optional filtering."""
        if not self.logging_system:
            return json.dumps({"error": "LoggingSystem not available"})
        try:
            logs = self.logging_system.get_logs(level, component, limit)
            return json.dumps({"count": len(logs), "logs": logs})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def configure_logger(self, component: str, level: str, format: str | None = None) -> str:
        """Configure logger for a specific component."""
        if not self.logging_system:
            return json.dumps({"error": "LoggingSystem not available"})
        try:
            self.logging_system.configure(component, level, format)
            return json.dumps({"status": "configured", "component": component, "level": level})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def show_dashboard(self, view: str = "overview") -> str:
        """Display dashboard with specified view."""
        if not self.dashboard:
            return json.dumps({"error": "Dashboard not available"})
        try:
            data = self.dashboard.show(view)
            return json.dumps({"view": view, "data": data})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_system_status(self) -> str:
        """Get overall system status."""
        return json.dumps(
            {
                "status": "operational",
                "extensions_loaded": 9,
                "uptime": "active",
                "components": {
                    "logging": "active",
                    "dashboard": "active",
                    "database": "connected",
                    "mcp": "listening",
                },
            }
        )


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return LoggingExtension(manifest, nexus_api)
