# Quick Reference: Using the New Components

## 🚀 Quick Start (5 minutes)

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Test
```bash
pytest tests/test_recommendations.py -v
```

### 3. Use in Your Code

---

## 💾 Caching

### Basic Usage
```python
from src.core.cache import cache_decorator, CacheManager

# Option 1: Decorator (recommended)
@cache_decorator(ttl_seconds=1800)
def expensive_function(param1, param2):
    return result

# Option 2: Manual control
cache = CacheManager()
cache.set("key", value, ttl_seconds=3600)
result = cache.get("key")
cache.delete("key")
cache.clear()
```

### Statistics
```python
cache = CacheManager()
stats = cache.get_stats()
print(stats)
# {'type': 'LRU', 'size': 42, 'hits': 1000, 'misses': 50, 'hit_rate': '95.24%'}
```

### Redis Setup (Optional)
```python
from src.core.cache import RedisCache, CacheManager

redis_cache = RedisCache(host="localhost", port=6379)
cache = CacheManager(backend=redis_cache)
# Automatically falls back to LRU if Redis unavailable
```

---

## ✔️ Validation

### Input Validation
```python
from src.core.validation import Validator, ValidationError

# Text validation
try:
    safe_text = Validator.validate_text(user_input, max_length=1000)
except ValidationError as e:
    print(f"Invalid: {e}")

# Query validation (prevents injection)
try:
    safe_query = Validator.validate_query(search_term)
except ValidationError as e:
    print(f"Suspicious query: {e}")

# Batch validation
try:
    docs = Validator.validate_batch(document_list, max_size=1000)
except ValidationError as e:
    print(f"Batch error: {e}")
```

### Pydantic Models (recommended for API)
```python
from src.core.validation import SearchQuery

# In FastAPI handler
@app.post("/search")
def search(query: SearchQuery):
    # Automatically validated and parsed
    return search_engine.find(query.text, limit=query.limit)
```

### Sanitization
```python
from src.core.validation import Validator

# Remove dangerous content
safe = Validator.sanitize_text(user_input)

# Validate email
try:
    email = Validator.validate_email(user_email)
except ValidationError:
    print("Invalid email")
```

---

## 🔄 Resilience

### Circuit Breaker
```python
from src.core.resilience import CircuitBreaker

breaker = CircuitBreaker(
    "api_service",
    failure_threshold=0.5,  # Open if >50% fail
    recovery_timeout=60     # Try recovery after 60s
)

@breaker
def call_external_api():
    return requests.get(url)

# Or manual
try:
    result = breaker.call(risky_function)
except CircuitBreakerError:
    print("Service temporarily unavailable")
```

### Retry with Backoff
```python
from src.core.resilience import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    base_delay=1.0,        # 1s, 2s, 4s delays
    jitter=True            # Add randomness
)
def unreliable_operation():
    return do_something()
```

### Timeout
```python
from src.core.resilience import TimeoutManager, TimeoutError

with TimeoutManager(timeout_seconds=5) as timeout:
    while processing:
        timeout.check_timeout()  # Raises if exceeded
        remaining = timeout.remaining()
        print(f"Time left: {remaining}s")
```

### Bulkhead (Concurrency Limit)
```python
from src.core.resilience import BulkheadIsolation

limiter = BulkheadIsolation(max_concurrent=10)

@limiter
def database_query():
    return db.query()

# Stats
stats = limiter.get_stats()
print(f"Active: {stats['active_count']}/{stats['max_concurrent']}")
```

### All Together
```python
from src.core.resilience import ResilientExecutor

executor = ResilientExecutor(
    timeout_seconds=30,
    max_retries=3
)

result = executor.execute(risky_function, arg1, arg2)
stats = executor.get_stats()
```

---

## 📋 Common Patterns

### API Endpoint with All Protections
```python
from fastapi import FastAPI
from src.core.validation import SearchQuery
from src.core.cache import cache_decorator
from src.core.resilience import ResilientExecutor

app = FastAPI()

@app.post("/search")
@cache_decorator(ttl_seconds=1800)
def search_endpoint(query: SearchQuery):
    # query is already validated by Pydantic
    
    executor = ResilientExecutor()
    
    # All resilience patterns applied
    return executor.execute(
        search_engine.find,
        query.text,
        limit=query.limit
    )
```

### NLP Pipeline
```python
@cache_decorator(ttl_seconds=3600)  # Cache embeddings
@retry_with_backoff(max_attempts=2)  # Handle transient errors
def analyze_text(text: str):
    validated = Validator.validate_text(text, max_length=10000)
    return nlp_pipeline.process(validated)
```

### External API Call
```python
breaker = CircuitBreaker("external_api")

@breaker
@retry_with_backoff(max_attempts=3, base_delay=2)
def fetch_from_api(url):
    with TimeoutManager(10) as timeout:
        response = requests.get(url, timeout=10)
        timeout.check_timeout()
        return response.json()
```

---

## 🔧 Configuration

### Cache Config
```yaml
# config.yaml
cache:
  enabled: true
  backend: redis  # or "lru"
  max_size: 5000
  default_ttl: 1800
  redis:
    host: localhost
    port: 6379
    db: 0
```

### Validation Config
```python
# Customize limits
Validator.MAX_TEXT_LENGTH = 20000  # Up from 10000
Validator.MAX_QUERY_LENGTH = 1000  # Up from 500
```

### Resilience Config
```python
# Customize thresholds
breaker = CircuitBreaker(
    "database",
    failure_threshold=0.3,  # More aggressive
    recovery_timeout=120    # Longer wait
)
```

---

## 🎯 Monitoring

### Cache Health
```python
cache = CacheManager()
stats = cache.get_stats()

# Check hit rate
if stats['hit_rate'] < 50:
    print("WARNING: Low cache hit rate")

# Monitor growth
if stats['size'] > stats['max_size'] * 0.9:
    print("WARNING: Cache near capacity")
```

### Circuit Breaker Health
```python
breaker = CircuitBreaker("api")
stats = breaker.get_stats()

if stats['state'] == 'open':
    print("ALERT: Circuit breaker OPEN")

print(f"Failure rate: {stats['failure_rate_percent']}")
```

### Validation Errors
```python
try:
    validated = Validator.validate_query(input)
except ValidationError as e:
    logger.warning(f"Validation failed: {e.message}")
    # Track metrics for security
```

---

## ⚡ Performance Tips

1. **Cache Aggressively**: Use decorator on all slow operations
   ```python
   @cache_decorator(ttl_seconds=3600)  # 1 hour
   def slow_operation():
       return expensive_computation()
   ```

2. **Validate Early**: Validate at API boundaries
   ```python
   # GOOD: Validate once at entry
   def api_handler(request: ValidatedSchema):
       process(request)  # Safe to use
   
   # BAD: Validate multiple times
   def internal_func(data):
       validate(data)  # Repeated work
   ```

3. **Circuit Breaker for External Calls**: Prevents cascade failures
   ```python
   # GOOD: Protect external API
   @CircuitBreaker("external_api")(external_call)
   
   # BAD: Circuit breaker on local operation
   @CircuitBreaker("local_db")(db.query)  # Unnecessary
   ```

4. **Tune Retry Delays**: Balance speed vs. reliability
   ```python
   # For fast failures: shorter delays
   @retry_with_backoff(base_delay=0.5)
   
   # For slow services: longer delays
   @retry_with_backoff(base_delay=5, max_delay=60)
   ```

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cache always misses" | Check TTL, verify key generation |
| "Validation too strict" | Adjust max_length in models |
| "Redis not available" | Falls back to LRU automatically |
| "Circuit breaker stuck open" | Call `.reset()` or wait timeout |
| "Retries keep failing" | Check base_delay, increase max_attempts |
| "Timeout never triggers" | Call `check_timeout()` in loop |
| "Bulkhead always full" | Increase max_concurrent or add queuing |

---

## 📚 Full Imports Reference

```python
# Caching
from src.core.cache import (
    CacheManager,
    LRUCache,
    RedisCache,
    cache_decorator,
    get_cache_manager,
    reset_cache,
)

# Validation
from src.core.validation import (
    Validator,
    ValidationError,
    SearchQuery,
    DocumentInput,
    AnalysisRequest,
    validate_input,
)

# Resilience
from src.core.resilience import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    retry_with_backoff,
    TimeoutManager,
    TimeoutError,
    BulkheadIsolation,
    ResilientExecutor,
    get_resilient_executor,
    reset_resilience,
)
```

---

## 🎓 Example: Complete Application

```python
from fastapi import FastAPI, HTTPException
from src.core.cache import cache_decorator
from src.core.validation import SearchQuery, Validator
from src.core.resilience import ResilientExecutor

app = FastAPI()
executor = ResilientExecutor(timeout_seconds=30, max_retries=2)

@app.post("/analyze")
@cache_decorator(ttl_seconds=3600)
def analyze(query: SearchQuery):
    try:
        # Pydantic auto-validates input
        text = query.text
        
        # Resilience + timeout + retry handling
        results = executor.execute(
            analyze_sentiment,
            text
        )
        
        return {"status": "success", "results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@executor.circuit_breaker
def analyze_sentiment(text: str):
    # Already validated by Pydantic
    return sentiment_model.predict(text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

**Last Updated:** January 21, 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅
