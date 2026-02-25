"""
Performance Optimization Utilities for SME Extensions

Provides utilities for performance monitoring, caching, and optimization
patterns to improve extension performance and resource usage.
"""

import asyncio
import collections
import functools
import hashlib
import json
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

import psutil

logger = logging.getLogger("SME.Performance")

T = TypeVar('T')

class LRUCache:
    """Thread-safe LRU Cache implementation for SME extensions."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: collections.OrderedDict[str, dict[str, Any]] = collections.OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> None | Any:
        """Get value from cache if it exists and is not expired."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if self._is_expired(entry):
                    del self.cache[key]
                    self.misses += 1
                    return None

                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return entry['value']

            self.misses += 1
            return None
    
    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = {
                'value': value,
                'timestamp': datetime.now()
            }

            # Remove oldest items if cache is full
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def _is_expired(self, entry: dict[str, Any]) -> bool:
        """Check if cache entry has expired."""
        age = datetime.now() - entry['timestamp']
        return bool(age.total_seconds() > self.ttl_seconds)
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': round(hit_rate, 2),
                'ttl_seconds': self.ttl_seconds
            }


class PerformanceMonitor:
    """Monitors and logs performance metrics for operations."""
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.operation_times: dict[str, list] = {}
        self.lock = threading.RLock()
    
    def time_operation(self, operation_name: str) -> 'OperationTimer':
        """Time a specific operation."""
        return OperationTimer(self, operation_name)
    
    def record_operation_time(self, operation_name: str, duration: float):
        """Record the duration of an operation."""
        with self.lock:
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []

            self.operation_times[operation_name].append(duration)

            # Keep only last 100 measurements
            if len(self.operation_times[operation_name]) > 100:
                self.operation_times[operation_name] = self.operation_times[operation_name][-100:]
    
    def get_operation_stats(self, operation_name: str) -> dict[str, Any]:
        """Get performance statistics for an operation."""
        with self.lock:
            if operation_name not in self.operation_times:
                return {'error': 'Operation not found'}
            
            times = self.operation_times[operation_name]
            if not times:
                return {'error': 'No data available'}

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            # Calculate percentiles
            sorted_times = sorted(times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            return {
                'operation': operation_name,
                'count': len(times),
                'avg_time': round(avg_time, 4),
                'min_time': round(min_time, 4),
                'max_time': round(max_time, 4),
                'p50_time': round(p50, 4),
                'p95_time': round(p95, 4),
                'p99_time': round(p99, 4)
            }
    
    def get_all_stats(self) -> dict[str, Any]:
        """Get performance statistics for all operations."""
        with self.lock:
            stats = {}
            for operation_name in self.operation_times:
                stats[operation_name] = self.get_operation_stats(operation_name)
            return stats


class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time: float | None = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.perf_counter() - self.start_time
            self.monitor.record_operation_time(self.operation_name, duration)


def cache_result(max_size: int = 100, ttl_seconds: int = 300):
    """
    Decorator to cache function results with LRU and TTL.
    
    Args:
        max_size: Maximum number of cached items
        ttl_seconds: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(max_size, ttl_seconds)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key = _create_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key = _create_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        # Store cache on function for access
        setattr(sync_wrapper, '_cache', cache)
        setattr(async_wrapper, '_cache', cache)
        
        # Add cache management methods
        def clear_cache():
            cache.clear()
        def get_cache_stats():
            return cache.get_stats()
        
        setattr(sync_wrapper, 'clear_cache', clear_cache)
        setattr(sync_wrapper, 'get_cache_stats', get_cache_stats)
        setattr(async_wrapper, 'clear_cache', clear_cache)
        setattr(async_wrapper, 'get_cache_stats', get_cache_stats)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _create_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Create a cache key from function name, args, and kwargs."""
    
    # Convert args and kwargs to a hashable string
    key_data = {
        'func': func_name,
        'args': args,
        'kwargs': kwargs
    }
    
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


class ResourceMonitor:
    """Monitor system resources and provide optimization suggestions."""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.resource_history = []
        self.lock = threading.Lock()
    
    def start_monitoring(self, interval_seconds: int = 30):
        """Start background resource monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval_seconds,), 
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop background resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self, interval_seconds: int):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                stats = self._collect_resource_stats()
                with self.lock:
                    self.resource_history.append(stats)
                    # Keep only last 100 entries
                    if len(self.resource_history) > 100:
                        self.resource_history = self.resource_history[-100:]
                
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _collect_resource_stats(self) -> dict[str, Any]:
        """Collect current resource usage statistics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Process-specific stats
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss / (1024**2)  # MB
            process_cpu = process.cpu_percent()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': round(memory_used_gb, 2),
                'memory_total_gb': round(memory_total_gb, 2),
                'disk_percent': disk_percent,
                'disk_free_gb': round(disk_free_gb, 2),
                'process_memory_mb': round(process_memory, 2),
                'process_cpu_percent': process_cpu
            }
        except Exception as e:
            logger.error(f"Failed to collect resource stats: {e}")
            return {'error': str(e)}
    
    def get_current_stats(self) -> dict[str, Any]:
        """Get current resource usage."""
        try:
            return self._collect_resource_stats()
        except Exception as e:
            return {'error': str(e)}
    
    def get_optimization_suggestions(self) -> list[str]:
        """Get optimization suggestions based on resource usage."""
        suggestions = []
        
        try:
            current = self.get_current_stats()
            if 'error' in current:
                return ['Unable to collect resource statistics']
            
            # CPU suggestions
            if current['cpu_percent'] > 80:
                suggestions.append("High CPU usage detected - consider optimizing algorithms or adding caching")
            
            # Memory suggestions
            if current['memory_percent'] > 80:
                suggestions.append("High memory usage detected - consider clearing caches or optimizing data structures")
            
            # Disk suggestions
            if current['disk_percent'] > 90:
                suggestions.append("Low disk space detected - consider cleaning up temporary files")
            
            # Process-specific suggestions
            if current['process_memory_mb'] > 1000:  # > 1GB
                suggestions.append("High process memory usage - consider implementing memory pooling")
            
            if not suggestions:
                suggestions.append("Resource usage is within normal ranges")
            
            return suggestions
            
        except Exception as e:
            return [f"Error generating suggestions: {e}"]
    
    def get_resource_history(self) -> list[dict[str, Any]]:
        """Get historical resource usage data."""
        with self.lock:
            return self.resource_history.copy()


class AsyncBatchProcessor:
    """Process items in batches with concurrency control."""
    
    def __init__(self, max_concurrent: int = 10, batch_size: int = 100):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_items(self, items: list, process_func: Callable, 
                          progress_callback: None | Callable = None) -> list:
        """
        Process items in batches with concurrency control.
        
        Args:
            items: List of items to process
            process_func: Async function to process each item
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of results
        """
        results = []
        
        # Process in batches
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await self._process_batch(batch, process_func)
            results.extend(batch_results)
            
            if progress_callback:
                await progress_callback(i + len(batch), len(items))
        
        return results
    
    async def _process_batch(self, batch: list, process_func: Callable) -> list:
        """Process a single batch with concurrency control."""
        async def process_with_semaphore(item):
            async with self.semaphore:
                return await process_func(item)
        
        tasks = [process_with_semaphore(item) for item in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)


# Global instances
_global_resource_monitor = ResourceMonitor()
_global_performance_monitors: dict[str, PerformanceMonitor] = {}
_global_caches: dict[str, LRUCache] = {}


def get_resource_monitor() -> ResourceMonitor:
    """Get the global resource monitor instance."""
    return _global_resource_monitor


def get_performance_monitor(plugin_id: str) -> PerformanceMonitor:
    """Get or create a performance monitor for a plugin."""
    if plugin_id not in _global_performance_monitors:
        _global_performance_monitors[plugin_id] = PerformanceMonitor(plugin_id)
    return _global_performance_monitors[plugin_id]


def get_cache(name: str, max_size: int = 1000, ttl_seconds: int = 300) -> LRUCache:
    """Get or create a named cache."""
    if name not in _global_caches:
        _global_caches[name] = LRUCache(max_size, ttl_seconds)
    return _global_caches[name]


def clear_all_caches():
    """Clear all global caches."""
    for cache in _global_caches.values():
        cache.clear()


def get_all_cache_stats() -> dict[str, Any]:
    """Get statistics for all caches."""
    stats = {}
    for name, cache in _global_caches.items():
        stats[name] = cache.get_stats()
    return stats


def get_all_performance_stats() -> dict[str, Any]:
    """Get performance statistics for all plugins."""
    stats = {}
    for plugin_id, monitor in _global_performance_monitors.items():
        stats[plugin_id] = monitor.get_all_stats()
    return stats