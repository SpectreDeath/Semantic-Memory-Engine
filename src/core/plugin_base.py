from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable

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
        self.plugin_id = manifest.get("plugin_id", self.__class__.__name__)

    @abstractmethod
    async def on_startup(self) -> None:
        """
        Lifecycle hook executed when the plugin is first loaded.
        Use this to initialize database tables, cache data, or warm up models.
        """
        pass

    @abstractmethod
    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lifecycle hook executed when new data is ingested into the system.
        
        Args:
            raw_data (str): The text content being ingested.
            metadata (Dict[str, Any]): Source metadata (e.g., origin, timestamp, source_id).
            
        Returns:
            Dict[str, Any]: The analysis results to be appended or merged. 
                            Must contain a "status" key.
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[Callable[..., Any]]:
        """
        Declares the functions this plugin exposes to the AI Agent (e.g., via MCP).
        
        Returns:
            List[Callable[..., Any]]: A list of (optionally async) functions that act as tools.
        """
        pass
