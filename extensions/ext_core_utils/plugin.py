import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.CoreUtils")

try:
    from src.core.file_service import FileService
except ImportError:
    FileService = None

try:
    from src.core.config import ConfigManager
except ImportError:
    ConfigManager = None

try:
    from src.core.cache import CacheManager
except ImportError:
    CacheManager = None

try:
    from src.core.batch_processor import BatchProcessor
except ImportError:
    BatchProcessor = None

try:
    from src.core.auth import AuthManager
except ImportError:
    AuthManager = None

try:
    from src.core.factory import FactoryPattern
except ImportError:
    FactoryPattern = None

try:
    from src.core.events import EventSystem
except ImportError:
    EventSystem = None


class CoreUtilsExtension(BasePlugin):
    """
    Core Utilities Extension for SME.
    Provides file service, configuration, caching, batch processing, authentication, factory, and event system.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.file_service = FileService() if FileService else None
        self.config = ConfigManager() if ConfigManager else None
        self.cache = CacheManager() if CacheManager else None
        self.batch = BatchProcessor() if BatchProcessor else None
        self.auth = AuthManager() if AuthManager else None
        self.factory = FactoryPattern() if FactoryPattern else None
        self.events = EventSystem() if EventSystem else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Core Utilities extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.read_file,
            self.write_file,
            self.get_config,
            self.set_config,
            self.cache_get,
            self.cache_set,
            self.authenticate,
            self.check_permissions,
            self.publish_event,
            self.subscribe_event,
        ]

    async def read_file(self, file_path: str) -> str:
        """Read a file and return its contents."""
        if not self.file_service:
            return json.dumps({"error": "FileService not available"})
        try:
            content = self.file_service.read_file(file_path)
            return json.dumps({"content": content, "path": file_path})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file."""
        if not self.file_service:
            return json.dumps({"error": "FileService not available"})
        try:
            self.file_service.write_file(file_path, content)
            return json.dumps({"status": "success", "path": file_path})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_config(self, key: str) -> str:
        """Get configuration value by key."""
        if not self.config:
            return json.dumps({"error": "ConfigManager not available"})
        try:
            value = self.config.get(key)
            return json.dumps({"key": key, "value": value})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def set_config(self, key: str, value: Any) -> str:
        """Set configuration value."""
        if not self.config:
            return json.dumps({"error": "ConfigManager not available"})
        try:
            self.config.set(key, value)
            return json.dumps({"status": "success", "key": key})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def cache_get(self, key: str) -> str:
        """Get value from cache."""
        if not self.cache:
            return json.dumps({"error": "CacheManager not available"})
        try:
            value = self.cache.get(key)
            return json.dumps({"key": key, "value": value})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> str:
        """Set value in cache with TTL."""
        if not self.cache:
            return json.dumps({"error": "CacheManager not available"})
        try:
            self.cache.set(key, value, ttl)
            return json.dumps({"status": "success", "key": key, "ttl": ttl})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def authenticate(self, username: str, password: str) -> str:
        """Authenticate user credentials."""
        if not self.auth:
            return json.dumps({"error": "AuthManager not available"})
        try:
            result = self.auth.authenticate(username, password)
            return json.dumps({"authenticated": result, "user": username})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def check_permissions(self, user: str, resource: str, action: str) -> str:
        """Check user permissions for an action on a resource."""
        if not self.auth:
            return json.dumps({"error": "AuthManager not available"})
        try:
            has_permission = self.auth.check_permissions(user, resource, action)
            return json.dumps(
                {"user": user, "resource": resource, "action": action, "allowed": has_permission}
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def publish_event(self, event_type: str, payload: dict[str, Any]) -> str:
        """Publish an event to the event system."""
        if not self.events:
            return json.dumps({"error": "EventSystem not available"})
        try:
            self.events.publish(event_type, payload)
            return json.dumps({"status": "published", "event_type": event_type})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def subscribe_event(self, event_type: str, callback_name: str) -> str:
        """Subscribe to an event type."""
        if not self.events:
            return json.dumps({"error": "EventSystem not available"})
        try:
            self.events.subscribe(event_type, callback_name)
            return json.dumps(
                {"status": "subscribed", "event_type": event_type, "callback": callback_name}
            )
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return CoreUtilsExtension(manifest, nexus_api)
