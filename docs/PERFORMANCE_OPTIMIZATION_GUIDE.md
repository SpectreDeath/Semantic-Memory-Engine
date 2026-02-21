# SME Extension Performance Optimization Guide

This guide explains how to use the performance optimization utilities provided by `src/utils/performance.py` to improve extension performance and resource usage.

## Overview

The performance utilities provide:

- **LRU Caching** with TTL for expensive operations
- **Performance monitoring** with timing and statistics
- **Resource monitoring** for system-level optimization
- **Async batch processing** with concurrency control
- **Decorators** for automatic caching and timing

## Quick Start

### Basic Caching

```python
from src.utils.performance import cache_result

class MyPlugin(BasePlugin):
    @cache_result(max_size=100, ttl_seconds=300)
    async def expensive_operation(self, data: str) -> Dict[str, Any]:
        # This result will be cached for 5 minutes
        result = await self._compute_expensive_result(data)
        return result
```

### Performance Monitoring

```python
from src.utils.performance import get_performance_monitor

class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self.monitor = get_performance_monitor(self.plugin_id)
    
    async def my_operation(self, data):
        with self.monitor.time_operation("my_operation"):
            result = await self._process_data(data)
            return result
```

### Resource Monitoring

```python
from src.utils.performance import get_resource_monitor

# Start global resource monitoring
resource_monitor = get_resource_monitor()
resource_monitor.start_monitoring(interval_seconds=30)

# Get current stats
stats = resource_monitor.get_current_stats()
print(f"CPU: {stats['cpu_percent']}%, Memory: {stats['memory_percent']}%")

# Get optimization suggestions
suggestions = resource_monitor.get_optimization_suggestions()
```

## Caching

### Function-Level Caching

```python
from src.utils.performance import cache_result

@cache_result(max_size=1000, ttl_seconds=600)  # 1000 items, 10 minutes TTL
async def get_analysis_result(self, text: str) -> Dict[str, Any]:
    # Expensive computation here
    return await self._analyze_text(text)

# Clear cache when needed
self.get_analysis_result.clear_cache()

# Get cache statistics
cache_stats = self.get_analysis_result.get_cache_stats()
print(f"Hit rate: {cache_stats['hit_rate']}%")
```

### Manual Caching

```python
from src.utils.performance import get_cache

class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self.text_cache = get_cache("text_analysis", max_size=500, ttl_seconds=1800)
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        # Check cache first
        cached_result = self.text_cache.get(text)
        if cached_result:
            return cached_result
        
        # Compute result
        result = await self._compute_analysis(text)
        
        # Store in cache
        self.text_cache.set(text, result)
        return result
```

## Performance Monitoring

### Operation Timing

```python
from src.utils.performance import OperationTimer

class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self.monitor = get_performance_monitor(self.plugin_id)
    
    async def process_batch(self, items: list) -> list:
        with self.monitor.time_operation("batch_processing"):
            results = []
            for item in items:
                result = await self._process_item(item)
                results.append(result)
            return results
```

### Performance Statistics

```python
# Get statistics for a specific operation
stats = self.monitor.get_operation_stats("batch_processing")
print(f"Average time: {stats['avg_time']}s")
print(f"95th percentile: {stats['p95_time']}s")

# Get all statistics
all_stats = self.monitor.get_all_stats()
for operation, op_stats in all_stats.items():
    print(f"{operation}: {op_stats['avg_time']}s avg")
```

## Resource Monitoring

### System Resource Tracking

```python
from src.utils.performance import get_resource_monitor

class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self.resource_monitor = get_resource_monitor()
    
    async def check_resources(self):
        stats = self.resource_monitor.get_current_stats()
        
        if stats['cpu_percent'] > 80:
            logger.warning("High CPU usage detected")
        
        if stats['memory_percent'] > 85:
            logger.warning("High memory usage detected")
            # Consider clearing caches
            self._clear_caches()
```

### Optimization Suggestions

```python
suggestions = self.resource_monitor.get_optimization_suggestions()
for suggestion in suggestions:
    logger.info(f"Optimization suggestion: {suggestion}")
```

## Async Batch Processing

### Concurrency Control

```python
from src.utils.performance import AsyncBatchProcessor

class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self.batch_processor = AsyncBatchProcessor(
            max_concurrent=5,  # Limit concurrent operations
            batch_size=100     # Process in batches of 100
        )
    
    async def process_large_dataset(self, items: list) -> list:
        async def process_item(item):
            return await self._analyze_item(item)
        
        results = await self.batch_processor.process_items(
            items, 
            process_item,
            progress_callback=self._on_progress
        )
        return results
    
    async def _on_progress(self, processed: int, total: int):
        progress = (processed / total) * 100
        logger.info(f"Processing progress: {progress:.1f}%")
```

## Performance Best Practices

### 1. Cache Expensive Operations

```python
# GOOD: Cache expensive computations
@cache_result(max_size=100, ttl_seconds=300)
async def compute_similarity(self, text1: str, text2: str) -> float:
    return await self._calculate_similarity(text1, text2)

# BAD: Recompute every time
async def compute_similarity(self, text1: str, text2: str) -> float:
    return await self._calculate_similarity(text1, text2)  # No caching
```

### 2. Monitor Performance-Critical Operations

```python
# GOOD: Time critical operations
async def process_ingestion(self, data: str):
    with self.monitor.time_operation("ingestion_processing"):
        result = await self._heavy_computation(data)
        return result

# BAD: No performance tracking
async def process_ingestion(self, data: str):
    result = await self._heavy_computation(data)
    return result
```

### 3. Use Resource Monitoring

```python
# GOOD: Monitor resource usage
async def process_batch(self, items: list):
    if self._is_resource_constrained():
        # Throttle processing
        await asyncio.sleep(1.0)
    
    return await self._process_items(items)

def _is_resource_constrained(self) -> bool:
    stats = self.resource_monitor.get_current_stats()
    return stats['cpu_percent'] > 90 or stats['memory_percent'] > 90

# BAD: No resource awareness
async def process_batch(self, items: list):
    return await self._process_items(items)
```

### 4. Implement Concurrency Control

```python
# GOOD: Limit concurrent operations
async def process_items_concurrently(self, items: list):
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
    
    async def process_with_limit(item):
        async with semaphore:
            return await self._process_item(item)
    
    tasks = [process_with_limit(item) for item in items]
    return await asyncio.gather(*tasks)

# BAD: Unbounded concurrency
async def process_items_concurrently(self, items: list):
    tasks = [self._process_item(item) for item in items]
    return await asyncio.gather(*tasks)  # Could overwhelm system
```

## Performance Patterns

### 1. Lazy Loading

```python
class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self._model = None
    
    async def get_model(self):
        if self._model is None:
            self._model = await self._load_expensive_model()
        return self._model
    
    async def analyze(self, text: str):
        model = await self.get_model()
        return await model.analyze(text)
```

### 2. Connection Pooling

```python
class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self._db_pool = None
    
    async def get_db_connection(self):
        if self._db_pool is None:
            self._db_pool = await self._create_connection_pool()
        return await self._db_pool.acquire()
    
    async def release_db_connection(self, conn):
        if self._db_pool:
            self._db_pool.release(conn)
```

### 3. Memory Management

```python
class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self._cache = {}
        self._max_cache_size = 1000
    
    def _clear_old_cache_entries(self):
        if len(self._cache) > self._max_cache_size:
            # Remove oldest entries
            keys_to_remove = list(self._cache.keys())[:-self._max_cache_size]
            for key in keys_to_remove:
                del self._cache[key]
    
    def _should_clear_cache(self) -> bool:
        stats = self.resource_monitor.get_current_stats()
        return stats['memory_percent'] > 80
```

## Performance Monitoring Dashboard

### Collecting Metrics

```python
class PerformanceDashboard:
    def __init__(self):
        self.metrics = {}
    
    def collect_plugin_metrics(self, plugin_id: str, monitor: PerformanceMonitor):
        stats = monitor.get_all_stats()
        self.metrics[plugin_id] = stats
    
    def collect_cache_metrics(self):
        cache_stats = get_all_cache_stats()
        self.metrics['caches'] = cache_stats
    
    def collect_resource_metrics(self):
        resource_monitor = get_resource_monitor()
        stats = resource_monitor.get_current_stats()
        self.metrics['resources'] = stats
    
    def generate_report(self) -> Dict[str, Any]:
        return {
            'timestamp': datetime.now().isoformat(),
            'plugins': self.metrics.get('plugins', {}),
            'caches': self.metrics.get('caches', {}),
            'resources': self.metrics.get('resources', {}),
            'optimization_suggestions': self._get_suggestions()
        }
    
    def _get_suggestions(self) -> List[str]:
        suggestions = []
        
        # Check cache hit rates
        for cache_name, stats in self.metrics.get('caches', {}).items():
            if stats['hit_rate'] < 50:
                suggestions.append(f"Cache '{cache_name}' has low hit rate ({stats['hit_rate']}%)")
        
        # Check operation performance
        for plugin_name, plugin_stats in self.metrics.get('plugins', {}).items():
            for op_name, op_stats in plugin_stats.items():
                if op_stats.get('avg_time', 0) > 1.0:  # > 1 second
                    suggestions.append(f"Operation '{op_name}' in '{plugin_name}' is slow ({op_stats['avg_time']}s)")
        
        return suggestions
```

## Migration Examples

### Before (No Performance Optimization)

```python
class OldPlugin(BasePlugin):
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        # No caching - always recompute
        result = await self._expensive_analysis(text)
        return result
    
    async def process_batch(self, items: list) -> list:
        # No concurrency control
        tasks = [self._process_item(item) for item in items]
        return await asyncio.gather(*tasks)
```

### After (With Performance Optimization)

```python
class NewPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self.monitor = get_performance_monitor(self.plugin_id)
        self.resource_monitor = get_resource_monitor()
        self.batch_processor = AsyncBatchProcessor(max_concurrent=5, batch_size=100)
    
    @cache_result(max_size=500, ttl_seconds=600)
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        with self.monitor.time_operation("text_analysis"):
            result = await self._expensive_analysis(text)
            return result
    
    async def process_batch(self, items: list) -> list:
        if self._should_throttle():
            await asyncio.sleep(0.5)
        
        return await self.batch_processor.process_items(
            items, 
            self._process_item,
            progress_callback=self._on_progress
        )
    
    def _should_throttle(self) -> bool:
        stats = self.resource_monitor.get_current_stats()
        return stats['cpu_percent'] > 80 or stats['memory_percent'] > 85
```

## Performance Testing

### Benchmarking

```python
import time
from src.utils.performance import get_performance_monitor

class PerformanceTester:
    def __init__(self):
        self.monitor = get_performance_monitor("PerformanceTester")
    
    async def benchmark_operation(self, operation_func, *args, iterations: int = 10):
        """Benchmark an operation over multiple iterations."""
        times = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            await operation_func(*args)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        logger.info(f"Benchmark results for {operation_func.__name__}:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Min: {min_time:.4f}s")
        logger.info(f"  Max: {max_time:.4f}s")
        
        return {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'times': times
        }
```

## Integration with Existing Extensions

The following extensions can be optimized using these utilities:

- **ext_governor** - Already updated with performance imports
- **ext_adversarial_tester** - Can add caching for expensive computations
- **ext_atlas** - Can cache T-SNE results and visualization data
- **ext_logic_auditor** - Can cache logical consistency checks
- **ext_tactical_forensics** - Can cache forensic analysis results
- **ext_sample_echo** - Can cache echo detection results
- **ext_immunizer** - Can cache signature hardening results
- **ext_archival_diff** - Can cache Wayback Machine queries

## Future Enhancements

- **Automatic performance profiling** during development
- **Memory leak detection** for long-running extensions
- **Database query optimization** suggestions
- **Network request batching** for external API calls
- **Real-time performance alerts** for production systems