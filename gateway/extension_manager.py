import os
import json
import logging
import importlib.util
import inspect
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("lawnmower.extension_manager")

class ExtensionManager:
    """
    Dynamic Plugin Loader for Lawnmower Man v1.1.1.
    Supports the class-based ForensicExtension boilerplate.
    """
    def __init__(self, nexus_api: Any, extensions_dir: Optional[str] = None):
        self.extensions_dir = os.path.normpath(
            extensions_dir
            or os.environ.get(
                "SME_EXTENSIONS_DIR",
                str(Path(__file__).resolve().parent.parent / "extensions"),
            )
        )
        self.nexus_api = nexus_api
        self.extensions: Dict[str, Any] = {}
        
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
                with open(manifest_path, 'r') as f:
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

    async def _load_module(self, plugin_id: str, path: str, manifest: Dict[str, Any]):
        """
        Dynamically import the module and call register_extension().
        """
        spec = importlib.util.spec_from_file_location(plugin_id, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, 'register_extension'):
                    # Call registration hook to get the plugin instance
                    plugin_instance = module.register_extension(manifest, self.nexus_api)
                    
                    # Run startup logic if defined
                    if hasattr(plugin_instance, 'on_startup'):
                        if inspect.iscoroutinefunction(plugin_instance.on_startup):
                            await plugin_instance.on_startup()
                        else:
                            plugin_instance.on_startup()
                    
                    self.extensions[plugin_id] = {
                        "manifest": manifest,
                        "instance": plugin_instance
                    }
                    logger.info(f"Successfully loaded plugin: {plugin_id} (v{manifest.get('version', '0.1')})")
                else:
                    logger.warning(f"Plugin {plugin_id}: register_extension() function not found.")
            except Exception as e:
                logger.error(f"Execution error in plugin {plugin_id}: {e}")

    def get_extension_tools(self) -> List[Dict[str, Any]]:
        """
        Aggregate all tools provided by loaded extensions.
        """
        all_tools = []
        for plugin_id, ext in self.extensions.items():
            instance = ext["instance"]
            if hasattr(instance, 'get_tools'):
                tools = instance.get_tools()
                for tool_func in tools:
                    # Introspect the tool function for metadata
                    all_tools.append({
                        "name": tool_func.__name__,
                        "description": tool_func.__doc__ or "No description provided.",
                        "handler": tool_func,
                        "plugin_id": plugin_id
                    })
        return all_tools

    async def notify_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Notify all plugins of a new ingestion event.
        """
        for ext in self.extensions.values():
            instance = ext["instance"]
            if hasattr(instance, 'on_ingestion'):
                try:
                    if inspect.iscoroutinefunction(instance.on_ingestion):
                        await instance.on_ingestion(raw_data, metadata)
                    else:
                        instance.on_ingestion(raw_data, metadata)
                except Exception as e:
                    logger.error(f"Error in on_ingestion hook for plugin: {e}")

    def get_status(self) -> List[Dict[str, Any]]:
        """
        Return status of all loaded extensions for the health check.
        """
        status = []
        for plugin_id, ext in self.extensions.items():
            instance = ext["instance"]
            tools_count = len(instance.get_tools()) if hasattr(instance, 'get_tools') else 0
            status.append({
                "id": plugin_id,
                "name": ext["manifest"].get("name", plugin_id),
                "version": ext["manifest"].get("version", "0.1"),
                "tools_count": tools_count
            })
        return status
