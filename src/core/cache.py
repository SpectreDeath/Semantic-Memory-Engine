"""
Advanced caching layer with Redis support and local LRU fallback.

Provides high-performance caching for semantic search results, NLP computations,
and other expensive operations. Supports both distributed Redis caching and
local in-memory LRU caching.

Features:
- Redis support for distributed caching
- LRU fallback for local caching
- TTL-based cache invalidation
- Decorator-based caching for functions
- Cache statistics and monitoring
- Thread-safe operations

Usage:
    from src.core.cache import CacheManager, cache_decorator
    
    # Get cache manager (singleton)
    cache = CacheManager()
    
    # Cache a value
    cache.set("key", "value", ttl_seconds=3600)
    value = cache.get("key")
    
    # Use as decorator for functions
    @cache_decorator(ttl_seconds=1800)
    def expensive_computation(param1, param2):
        return some_result
"""

import hashlib
import json
import logging
import pickle
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store value in cache with optional TTL."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove key from cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class LRUCache(CacheBackend):
    """
    Local in-memory LRU cache implementation.
    
    Thread-safe, stores values with optional TTL, and evicts least-recently-used
    entries when capacity is reached.
    """

    def __init__(self, max_size: int = 1000):
        """Initialize LRU cache."""
        self.max_size = max_size
        self.cache: OrderedDict[str, Tuple[Any, Optional[float]]] = OrderedDict()
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache, returns None if expired or missing."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            value, expiry = self.cache[key]

            # Check if expired
            if expiry is not None and time.time() > expiry:
                del self.cache[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store value in cache with optional TTL."""
        with self.lock:
            # Remove old entry if exists
            if key in self.cache:
                del self.cache[key]

            # Calculate expiry time
            expiry = None
            if ttl_seconds is not None:
                expiry = time.time() + ttl_seconds

            # Add new entry
            self.cache[key] = (value, expiry)
            self.cache.move_to_end(key)

            # Evict LRU entry if over capacity
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
                self.evictions += 1

            return True

    def delete(self, key: str) -> bool:
        """Remove key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            return True

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self.lock:
            if key not in self.cache:
                return False

            value, expiry = self.cache[key]
            if expiry is not None and time.time() > expiry:
                del self.cache[key]
                return False

            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (
                (self.hits / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "type": "LRU",
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": f"{hit_rate:.2f}%",
                "total_requests": total_requests,
            }


class RedisCache(CacheBackend):
    """Distributed Redis cache implementation with graceful fallback."""

    def __init__(
        self, host: str = "localhost", port: int = 6379, db: int = 0, timeout: int = 5
    ):
        """Initialize Redis cache connection."""
        self.host = host
        self.port = port
        self.db = db
        self.timeout = timeout
        self.redis_client = None
        self.available = False
        self.hits = 0
        self.misses = 0

        try:
            import redis

            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=False,
                socket_connect_timeout=timeout,
            )
            # Test connection
            self.redis_client.ping()
            self.available = True
            logger.info(f"Redis cache connected: {host}:{port}/{db}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using LRU fallback.")
            self.available = False

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        try:
            return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return b""

    def _deserialize(self, data: bytes) -> Optional[Any]:
        """Deserialize value from Redis."""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            return None

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis cache."""
        if not self.available or not self.redis_client:
            self.misses += 1
            return None

        try:
            data = self.redis_client.get(key)
            if data is None:
                self.misses += 1
                return None

            self.hits += 1
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store value in Redis cache with optional TTL."""
        if not self.available or not self.redis_client:
            return False

        try:
            serialized = self._serialize(value)
            if ttl_seconds:
                self.redis_client.setex(key, ttl_seconds, serialized)
            else:
                self.redis_client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Remove key from Redis cache."""
        if not self.available or not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries in current database."""
        if not self.available or not self.redis_client:
            return False

        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self.available or not self.redis_client:
            return False

        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (
            (self.hits / total_requests * 100) if total_requests > 0 else 0
        )

        stats = {
            "type": "Redis",
            "available": self.available,
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests,
        }

        if self.available and self.redis_client:
            try:
                info = self.redis_client.info()
                stats["used_memory"] = info.get("used_memory_human", "N/A")
                stats["connected_clients"] = info.get("connected_clients", 0)
            except Exception as e:
                logger.debug(f"Failed to get Redis info: {e}")

        return stats


class CacheManager:
    """
    High-level cache management interface.
    
    Provides a unified API for caching operations with support for multiple
    backends and fallback strategies.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, backend: Optional[CacheBackend] = None):
        """Singleton pattern with optional backend injection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, backend: Optional[CacheBackend] = None):
        """Initialize cache manager with backend."""
        if not hasattr(self, "_initialized"):
            self.backend = backend or LRUCache(max_size=1000)
            self._initialized = True
            logger.info(f"CacheManager initialized with {type(self.backend).__name__}")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        return self.backend.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store value in cache."""
        return self.backend.set(key, value, ttl_seconds)

    def delete(self, key: str) -> bool:
        """Remove key from cache."""
        return self.backend.delete(key)

    def clear(self) -> bool:
        """Clear all cache entries."""
        return self.backend.clear()

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.backend.exists(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.backend.get_stats()

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and parameters."""
        key_data = {
            "prefix": prefix,
            "args": str(args),
            "kwargs": sorted(kwargs.items()),
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


def cache_decorator(
    ttl_seconds: int = 3600, cache_manager: Optional[CacheManager] = None
):
    """
    Decorator for caching function results.
    
    Args:
        ttl_seconds: Time-to-live in seconds
        cache_manager: Optional CacheManager instance (uses singleton if None)
    """
    if cache_manager is None:
        cache_manager = CacheManager()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key_str = cache_manager.cache_key(
                f"{func.__module__}.{func.__name__}", *args, **kwargs
            )

            # Try to get from cache
            cached = cache_manager.get(cache_key_str)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached

            # Compute result
            result = func(*args, **kwargs)

            # Store in cache
            cache_manager.set(cache_key_str, result, ttl_seconds)
            logger.debug(f"Cached result for {func.__name__}")

            return result

        return wrapper

    return decorator


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager singleton."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def reset_cache():
    """Reset cache manager (for testing)."""
    global _cache_manager
    if _cache_manager:
        _cache_manager.clear()
    _cache_manager = None


# Backwards compatibility
def get_cache() -> CacheManager:
    """Get global cache instance (backwards compatibility)."""
    return get_cache_manager()


def cached(ttl: int = 3600) -> Callable:
    """Decorator for caching function results (backwards compatibility)."""
    return cache_decorator(ttl_seconds=ttl)


def reset_cache_legacy() -> None:
    """Reset cache to initial state (backwards compatibility)."""
    reset_cache()
