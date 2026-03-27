from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger("lawnmower.extension_manager")


class DefaultExtensionContext:
    """
    Minimal NexusAPI implementation for when nexus_api is None (e.g. tests).
    Provides nexus (DB) and get_hsm() without extensions importing gateway.
    """

    def __init__(self):
        self._nexus = None

    @property
    def nexus(self):
        if self._nexus is None:
            from gateway.nexus_db import get_nexus

            self._nexus = get_nexus()
        return self._nexus

    def get_hsm(self):
        from gateway.hardware_security import get_hsm

        return get_hsm()


class ExtensionManager:
    """
    Dynamic Plugin Loader for Lawnmower Man v1.1.1.
    Discovers extensions via manifest.json and loads entry_point (default plugin.py).
    Each module must define register_extension(manifest, nexus_api) returning the plugin instance.
    Instance contract: get_tools() required; on_startup/on_ingestion optional.
    See docs/EXTENSION_CONTRACT.md for full vs minimal (BasePlugin) contract.
    """

    allowed_imports: ClassVar[list[str]] = [
        "gateway",
        "gateway.*",
        "src",
        "src.*",
        "pydantic",
        "fastapi",
        "httpx",
        "logging",
    ]

    restricted_imports: ClassVar[list[str]] = [
        # Only block truly dangerous imports that could harm the host
        # "os", "sys", "subprocess", "socket", "threading", "multiprocessing", "ctypes" are too aggressive
        # Most extensions legitimately need these standard library modules
    ]

    _forbidden_builtins: ClassVar[list[str]] = [
        "open",
        "compile",
        "eval",
        "exec",
        "__import__",
    ]

    def __init__(self, nexus_api: Any, extensions_dir: str | None = None):
        self.extensions_dir = os.path.normpath(
            extensions_dir
            or os.environ.get(
                "SME_EXTENSIONS_DIR",
                str(Path(__file__).resolve().parent.parent / "extensions"),
            )
        )
        self.nexus_api = nexus_api if nexus_api is not None else DefaultExtensionContext()
        self.extensions: dict[str, Any] = {}

        if not os.path.exists(self.extensions_dir):
            os.makedirs(self.extensions_dir, exist_ok=True)

    async def discover_and_load(self):
        """
        Recursively scan for manifest.json and load corresponding Python modules.
        """
        logger.info(f"ExtensionManager: Scanning {self.extensions_dir} for plugins...")

        for item in os.listdir(self.extensions_dir):
            plugin_path = os.path.join(self.extensions_dir, item)
            if not os.path.isdir(plugin_path):
                continue

            manifest_path = os.path.join(plugin_path, "manifest.json")
            if not os.path.exists(manifest_path):
                continue

            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)

                plugin_id = manifest.get("plugin_id", item)
                entry_point = manifest.get("entry_point", "plugin.py")
                module_path = os.path.join(plugin_path, entry_point)

                if os.path.exists(module_path):
                    await self._load_module(plugin_id, module_path, manifest)
                else:
                    logger.warning(f"Plugin {plugin_id}: Entry point {entry_point} not found.")

            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_path}: {e}")

    async def _load_module(self, plugin_id: str, path: str, manifest: dict[str, Any]):
        """
        Dynamically import the module and call register_extension().
        Uses standard import for reliable relative import support.
        """
        # Calculate module name (e.g., 'extensions.ext_social_intel.plugin')
        ext_folder = Path(path).parent.name
        module_name = f"extensions.{ext_folder}.plugin"

        try:
            # Ensure extensions directory is in sys.path for proper module resolution
            extensions_dir = str(Path(path).parent.parent)
            if extensions_dir not in sys.path:
                sys.path.insert(0, extensions_dir)

            # Import the module using standard import
            # This handles relative imports properly
            import importlib

            module = importlib.import_module(module_name)

            # Call register_extension if available
            if hasattr(module, "register_extension"):
                plugin_instance = module.register_extension(manifest, self.nexus_api)

                if hasattr(plugin_instance, "on_startup"):
                    if inspect.iscoroutinefunction(plugin_instance.on_startup):
                        await plugin_instance.on_startup()
                    else:
                        plugin_instance.on_startup()

                self.extensions[plugin_id] = {"manifest": manifest, "instance": plugin_instance}
                logger.info(
                    f"Successfully loaded plugin via package: {module_name} (v{manifest.get('version', '0.1')})"
                )
            else:
                logger.warning(
                    f"Plugin {plugin_id}: register_extension() not found in {module_name}"
                )
        except Exception as e:
            logger.error(f"Failed to load package-based plugin {plugin_id}: {e}")

    def get_extension_tools(self) -> list[dict[str, Any]]:
        """
        Aggregate all tools provided by loaded extensions.
        """
        all_tools = []
        for plugin_id, ext in self.extensions.items():
            instance = ext["instance"]
            if hasattr(instance, "get_tools"):
                tools = instance.get_tools()
                if isinstance(tools, dict):
                    for name, tool_func in tools.items():
                        all_tools.append(
                            {
                                "name": name,
                                "description": getattr(tool_func, "__doc__", None)
                                or "No description provided.",
                                "handler": tool_func,
                                "plugin_id": plugin_id,
                            }
                        )
                else:
                    for tool_func in tools:
                        all_tools.append(
                            {
                                "name": tool_func.__name__,
                                "description": tool_func.__doc__ or "No description provided.",
                                "handler": tool_func,
                                "plugin_id": plugin_id,
                            }
                        )
        return all_tools

    async def notify_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        """
        Notify all plugins of a new ingestion event.
        Calls on_ingestion(raw_data, metadata) for each plugin that defines it.
        Return values are not aggregated; fire-and-forget.
        """
        for ext in self.extensions.values():
            instance = ext["instance"]
            if hasattr(instance, "on_ingestion"):
                try:
                    if inspect.iscoroutinefunction(instance.on_ingestion):
                        await instance.on_ingestion(raw_data, metadata)
                    else:
                        instance.on_ingestion(raw_data, metadata)
                except Exception as e:
                    logger.error(f"Error in on_ingestion hook for plugin: {e}")

    async def fire_event(self, event_id: str, payload: dict[str, Any]):
        """
        Broadcast an event to all plugins that implement on_event.
        """
        tasks = []
        for plugin_id, ext in self.extensions.items():
            instance = ext["instance"]
            if hasattr(instance, "on_event"):
                try:
                    if inspect.iscoroutinefunction(instance.on_event):
                        tasks.append(instance.on_event(event_id, payload))
                    else:
                        instance.on_event(event_id, payload)
                except Exception as e:
                    logger.error(f"Error firing event {event_id} to {plugin_id}: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_status(self) -> list[dict[str, Any]]:
        """
        Return status of all loaded extensions for the health check.
        """
        status = []
        for plugin_id, ext in self.extensions.items():
            instance = ext["instance"]
            tools_count = len(instance.get_tools()) if hasattr(instance, "get_tools") else 0
            status.append(
                {
                    "id": plugin_id,
                    "name": ext["manifest"].get("name", plugin_id),
                    "version": ext["manifest"].get("version", "0.1"),
                    "tools_count": tools_count,
                }
            )
        return status
