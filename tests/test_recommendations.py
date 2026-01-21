"""
Tests for caching, validation, and resilience components.

Verifies performance, fault tolerance, and security enhancements.
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.core.cache import CacheManager, LRUCache, cache_decorator, get_cache_manager
from src.core.validation import Validator, ValidationError, validate_input
from src.core.resilience import (
    CircuitBreaker,
    retry_with_backoff,
    TimeoutManager,
    BulkheadIsolation,
    ResilientExecutor,
    CircuitBreakerError,
)


# ============================================================================
# CACHE TESTS
# ============================================================================


class TestLRUCache:
    """Tests for LRU cache implementation."""

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_ttl_expiration(self):
        """Test that cached items expire after TTL."""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1", ttl_seconds=1)
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_cache_lru_eviction(self):
        """Test that oldest entries are evicted when capacity is exceeded."""
        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert "hit_rate" in stats


class TestCacheDecorator:
    """Tests for cache decorator."""

    def test_decorator_caches_results(self):
        """Test that decorator caches function results."""
        call_count = 0
        
        @cache_decorator(ttl_seconds=10)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call - executes function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call - returns cached result
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Not incremented

    def test_decorator_different_args(self):
        """Test that decorator distinguishes different arguments."""
        call_count = 0
        
        @cache_decorator(ttl_seconds=10)
        def add(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        result1 = add(1, 2)
        result2 = add(2, 3)
        
        assert result1 == 3
        assert result2 == 5
        assert call_count == 2  # Called twice with different args


# ============================================================================
# VALIDATION TESTS
# ============================================================================


class TestValidator:
    """Tests for input validation."""

    def test_validate_text_valid(self):
        """Test validation of valid text."""
        result = Validator.validate_text("Hello World")
        assert result == "Hello World"

    def test_validate_text_too_short(self):
        """Test validation fails for text too short."""
        with pytest.raises(ValidationError):
            Validator.validate_text("", min_length=1)

    def test_validate_text_too_long(self):
        """Test validation fails for text too long."""
        with pytest.raises(ValidationError):
            Validator.validate_text("x" * 1001, max_length=1000)

    def test_validate_query_sql_injection_detection(self):
        """Test SQL injection detection in queries."""
        with pytest.raises(ValidationError):
            Validator.validate_query("SELECT * FROM users")

    def test_validate_query_xss_detection(self):
        """Test XSS detection in queries."""
        with pytest.raises(ValidationError):
            Validator.validate_query("<script>alert('xss')</script>")

    def test_validate_number_valid(self):
        """Test validation of valid numbers."""
        result = Validator.validate_number(42)
        assert result == 42.0

    def test_validate_number_out_of_range(self):
        """Test validation fails for out-of-range numbers."""
        with pytest.raises(ValidationError):
            Validator.validate_number(150, min_val=0, max_val=100)

    def test_sanitize_text(self):
        """Test text sanitization."""
        dirty = "Hello<script>alert('xss')</script> World"
        clean = Validator.sanitize_text(dirty)
        assert "<script>" not in clean
        assert "Hello" in clean

    def test_validate_batch_valid(self):
        """Test batch validation."""
        batch = ["doc1", "doc2", "doc3"]
        result = Validator.validate_batch(batch)
        assert len(result) == 3

    def test_validate_batch_too_large(self):
        """Test batch validation fails for oversized batch."""
        batch = ["doc"] * 1001
        with pytest.raises(ValidationError):
            Validator.validate_batch(batch, max_size=1000)

    def test_validate_email_valid(self):
        """Test email validation."""
        email = Validator.validate_email("user@example.com")
        assert email == "user@example.com"

    def test_validate_email_invalid(self):
        """Test email validation fails for invalid email."""
        with pytest.raises(ValidationError):
            Validator.validate_email("invalid.email")


# ============================================================================
# RESILIENCE TESTS
# ============================================================================


class TestCircuitBreaker:
    """Tests for circuit breaker."""

    def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker in normal operation."""
        breaker = CircuitBreaker("test")
        result = breaker.call(lambda: "success")
        assert result == "success"

    def test_circuit_breaker_opens_on_failure(self):
        """Test circuit breaker opens after failures."""
        breaker = CircuitBreaker("test", failure_threshold=0.5)
        
        def failing_func():
            raise ValueError("test error")
        
        # Fail once
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        
        # Circuit should open after 2 failures (failure rate > 0.5)
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        
        # Should now raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            breaker.call(lambda: "success")

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery."""
        breaker = CircuitBreaker("test", failure_threshold=0.5, recovery_timeout=1)
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(lambda: 1/0)
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should be in HALF_OPEN state and allow recovery
        result = breaker.call(lambda: "recovered")
        assert result == "recovered"

    def test_circuit_breaker_stats(self):
        """Test circuit breaker statistics."""
        breaker = CircuitBreaker("test")
        breaker.call(lambda: "success")
        breaker.call(lambda: "success")
        
        stats = breaker.get_stats()
        assert stats["successes"] == 2
        assert stats["state"] == "closed"


class TestRetryWithBackoff:
    """Tests for retry decorator."""

    def test_retry_succeeds_on_first_attempt(self):
        """Test retry decorator on successful call."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_retries_on_failure(self):
        """Test retry decorator retries on failure."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "success"
        
        result = failing_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausts_attempts(self):
        """Test retry decorator exhausts attempts."""
        @retry_with_backoff(max_attempts=2, base_delay=0.01)
        def always_fails():
            raise ValueError("always fails")
        
        with pytest.raises(ValueError):
            always_fails()


class TestTimeoutManager:
    """Tests for timeout manager."""

    def test_timeout_check_valid(self):
        """Test timeout check passes within limit."""
        with TimeoutManager(1.0) as tm:
            tm.check_timeout()  # Should not raise

    def test_timeout_check_expires(self):
        """Test timeout check raises when exceeded."""
        from src.core.resilience import TimeoutError
        
        with TimeoutManager(0.1) as tm:
            time.sleep(0.15)
            with pytest.raises(TimeoutError):
                tm.check_timeout()

    def test_timeout_remaining(self):
        """Test remaining timeout calculation."""
        with TimeoutManager(1.0) as tm:
            remaining = tm.remaining()
            assert 0 < remaining <= 1.0


class TestBulkheadIsolation:
    """Tests for bulkhead isolation."""

    def test_bulkhead_allows_up_to_limit(self):
        """Test bulkhead allows concurrent requests up to limit."""
        bulkhead = BulkheadIsolation(max_concurrent=2)
        
        assert bulkhead.acquire()
        assert bulkhead.acquire()
        assert not bulkhead.acquire()  # Max reached
        
        bulkhead.release()
        assert bulkhead.acquire()

    def test_bulkhead_stats(self):
        """Test bulkhead statistics."""
        bulkhead = BulkheadIsolation(max_concurrent=5)
        bulkhead.acquire()
        bulkhead.acquire()
        
        stats = bulkhead.get_stats()
        assert stats["active_count"] == 2
        assert stats["available"] == 3


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for all components."""

    def test_caching_improves_performance(self):
        """Test that caching improves performance."""
        cache = CacheManager()
        call_count = 0
        
        @cache_decorator(ttl_seconds=10)
        def expensive_op():
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)
            return "result"
        
        # First call is slow
        start = time.time()
        expensive_op()
        first_duration = time.time() - start
        
        # Second call should be fast (cached)
        start = time.time()
        expensive_op()
        cached_duration = time.time() - start
        
        assert cached_duration < first_duration / 2

    def test_validation_prevents_injection(self):
        """Test that validation prevents injection attacks."""
        dangerous_inputs = [
            "SELECT * FROM users",
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
        ]
        
        for dangerous in dangerous_inputs:
            with pytest.raises(ValidationError):
                Validator.validate_query(dangerous)

    def test_resilience_handles_failures(self):
        """Test resilience patterns handle failures gracefully."""
        executor = ResilientExecutor(max_retries=2)
        call_count = 0
        
        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temp error")
            return "success"
        
        result = executor.execute(sometimes_fails)
        assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
