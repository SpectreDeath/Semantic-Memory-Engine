"""
Ghost Trap Extension Plugin

Main plugin entry point that integrates the Ghost Trap extension
with the SME system.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from src.core.plugin_base import BasePlugin
    from src.utils.error_handling import ErrorHandler
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from plugin_base import BasePlugin
    from error_handling import ErrorHandler

try:
    from .ghost_detector import GhostDetector, GhostFile, scan_for_ghosts
    from .persistence_monitor import (
        get_monitoring_status,
        ghost_monitor,
        hook_governor_task_execution,
    )
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from ghost_detector import GhostDetector, GhostFile, scan_for_ghosts
    from persistence_monitor import (
        get_monitoring_status,
        ghost_monitor,
        hook_governor_task_execution,
    )

logger = logging.getLogger("LawnmowerMan.GhostTrap")


class GhostTrapPlugin(BasePlugin):
    """Main plugin class for the Ghost Trap extension."""

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.name = "Ghost Trap Extension"
        self.version = "1.0.0"
        self.description = (
            "Monitors for potential self-replication events and unauthorized file creation"
        )
        self.error_handler = ErrorHandler(self.plugin_id)

        self.config = {
            "size_threshold_mb": 100,
            "recursive_scan": True,
            "detailed_reports": True,
            "monitoring_enabled": True,
        }

        self.is_active = False

    def activate(self) -> bool:
        """Activate the Ghost Trap plugin."""
        try:
            logger.info("Activating %s v%s", self.name, self.version)
            logger.info("Description: %s", self.description)

            if self.config.get("monitoring_enabled", True):
                ghost_monitor.start_monitoring()
                logger.info("Persistence monitoring activated")

            self.is_active = True
            logger.info("%s activated successfully", self.name)
            return True

        except Exception as e:
            logger.exception("Failed to activate %s: %s", self.name, e)
            return False

    def deactivate(self) -> bool:
        """Deactivate the Ghost Trap plugin."""
        try:
            logger.info("Deactivating %s", self.name)

            ghost_monitor.stop_monitoring()
            logger.info("Persistence monitoring deactivated")

            self.is_active = False
            logger.info("%s deactivated successfully", self.name)
            return True

        except Exception as e:
            logger.exception("Failed to deactivate %s: %s", self.name, e)
            return False

    def get_status(self) -> dict[str, Any]:
        """Get current plugin status."""
        return {
            "name": self.name,
            "version": self.version,
            "is_active": self.is_active,
            "monitoring_status": get_monitoring_status(),
            "config": self.config,
        }

    def configure(self, **kwargs) -> bool:
        """Configure the plugin."""
        try:
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value

            logger.info("%s configuration updated", self.name)
            return True

        except Exception as e:
            logger.exception("Failed to configure %s: %s", self.name, e)
            return False

    def get_tools(self) -> list[Callable]:
        """Get available tools provided by this plugin."""
        return [self._create_scan_tool()]

    def _create_scan_tool(self) -> Callable:
        """Create the scan_for_ghosts tool with current configuration."""

        def scan_tool(
            project_root: str | None = None,
            size_threshold_mb: int | None = None,
            recursive: bool | None = None,
            detailed_report: bool | None = None,
        ) -> dict[str, Any]:
            """
            Scan for ghost files in the project.

            Args:
                project_root: Root directory to scan. If None, uses current working directory.
                size_threshold_mb: Minimum file size in MB to consider as suspicious.
                recursive: Whether to scan subdirectories recursively.
                detailed_report: Whether to print a detailed report.

            Returns:
                Dictionary containing scan results and summary.
            """
            scan_config = {
                "project_root": project_root or os.getcwd(),
                "size_threshold_mb": size_threshold_mb or self.config["size_threshold_mb"],
                "recursive": recursive if recursive is not None else self.config["recursive_scan"],
                "detailed_report": detailed_report
                if detailed_report is not None
                else self.config["detailed_reports"],
            }

            logger.info("Ghost Trap: Starting scan with config: %s", scan_config)
            return scan_for_ghosts(**scan_config)

        return scan_tool

    def get_hooks(self) -> dict[str, Callable]:
        """Get available hooks provided by this plugin."""
        return {"governor_task_execution": hook_governor_task_execution}

    def get_events(self) -> list[str]:
        """Get list of events this plugin can handle."""
        return [
            "task_execution_started",
            "task_execution_completed",
            "file_created",
            "ghost_detected",
        ]

    def handle_event(self, event_name: str, **kwargs) -> Any:
        """Handle plugin-specific events."""
        if event_name == "task_execution_started":
            if self.config.get("monitoring_enabled", True):
                ghost_monitor.start_monitoring()
                return {"monitoring_started": True}

        elif event_name == "task_execution_completed":
            if self.config.get("monitoring_enabled", True):
                ghost_monitor.stop_monitoring()
                return {"monitoring_stopped": True}

        elif event_name == "file_created":
            file_path = kwargs.get("file_path", "")
            if file_path and self._is_suspicious_file(file_path):
                logger.warning("Suspicious file created: %s", file_path)
                return {"suspicious_file_detected": True}

        elif event_name == "ghost_detected":
            ghost_info = kwargs.get("ghost_info", {})
            logger.warning("Ghost detected: %s", ghost_info)
            return {"ghost_handled": True}

        return {"event_handled": False}

    def _is_suspicious_file(self, file_path: str) -> bool:
        """Check if a newly created file is suspicious."""
        path = Path(file_path)

        if path.suffix.lower() not in {".bin", ".json"}:
            return False

        if ghost_monitor._is_hidden_directory(str(path)):
            return True

        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > self.config["size_threshold_mb"]:
                return True
        except OSError:
            pass

        return False


ghost_trap_plugin = GhostTrapPlugin({}, None)


def get_plugin(manifest: dict[str, Any] | None = None, nexus_api: Any | None = None) -> GhostTrapPlugin:
    """Get the global Ghost Trap plugin instance."""
    return GhostTrapPlugin(manifest or {}, nexus_api)


def register_extension(manifest: dict[str, Any], nexus_api: Any) -> GhostTrapPlugin:
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return GhostTrapPlugin(manifest, nexus_api)


__all__ = ["GhostTrapPlugin", "get_plugin", "ghost_trap_plugin", "register_extension"]