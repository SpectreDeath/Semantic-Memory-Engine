"""
Test suite for Tier 1 improvements.

Tests cache layer, input validation, circuit breaker, and rate limiting.
"""

import pytest
import time
from src.core.cache import CacheManager, cached, get_cache, reset_cache
from src.core.validation import Validator, ValidationError
from src.core.resilience import CircuitBreaker, CircuitBreakerError, CircuitState


# ==================== Cache Tests ====================

class TestCacheManager:
    """Tests for CacheManager."""
    
    def setup_method(self):
        """Reset cache before each test."""
        reset_cache()
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get."""
        cache = get_cache()
        cache.set("key1", "value1", ttl=60)
        
        result = cache.get("key1")
        assert result == "value1"
        assert cache.hits == 1
        assert cache.misses == 0
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = get_cache()
        result = cache.get("nonexistent")
        
        assert result is None
        assert cache.misses == 1
    
    def test_cache_with_fetch_fn(self):
        """Test cache with fetch function."""
        cache = get_cache()
        
        def expensive_fn():
            return "computed_value"
        
        # First call computes
        result1 = cache.get("key", expensive_fn, ttl=60)
        assert result1 == "computed_value"
        assert cache.misses == 1
        
        # Second call uses cache
        result2 = cache.get("key", expensive_fn, ttl=60)
        assert result2 == "computed_value"
        assert cache.hits == 1
    
    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        cache = get_cache()
        cache.set("key", "value", ttl=1)  # 1 second TTL
        
        # Should be in cache
        assert cache.get("key") == "value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("key") is None
    
    def test_cache_invalidate(self):
        """Test cache invalidation by pattern."""
        cache = get_cache()
        cache.set("user:1:profile", "data1")
        cache.set("user:1:settings", "data2")
        cache.set("user:2:profile", "data3")
        
        assert len(cache.cache) == 3
        
        # Invalidate user:1:*
        invalidated = cache.invalidate("user:1:")
        assert invalidated == 2
        assert len(cache.cache) == 1
    
    def test_cache_max_size(self):
        """Test cache max size eviction."""
        cache = CacheManager(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert len(cache.cache) == 3
        
        # Adding 4th should evict oldest
        cache.set("key4", "value4")
        assert len(cache.cache) == 3
        assert "key1" not in cache.cache  # Oldest should be removed
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = get_cache()
        
        cache.get("key1", lambda: "value1")  # Miss
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        
        stats = cache.stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total_requests'] == 3
        assert "66.67%" in stats['hit_rate']


class TestCachedDecorator:
    """Tests for @cached decorator."""
    
    def setup_method(self):
        """Reset cache before each test."""
        reset_cache()
    
    def test_cached_decorator(self):
        """Test @cached decorator functionality."""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_fn(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        assert expensive_fn(5) == 10
        assert call_count == 1
        
        # Second call (cached)
        assert expensive_fn(5) == 10
        assert call_count == 1  # Should not increment
        
        # Different args
        assert expensive_fn(10) == 20
        assert call_count == 2


# ==================== Validation Tests ====================

class TestValidator:
    """Tests for Validator."""
    
    def test_validate_text_valid(self):
        """Test valid text validation."""
        text = "This is valid text"
        result = Validator.validate_text(text)
        assert result == text
    
    def test_validate_text_empty(self):
        """Test empty text validation."""
        with pytest.raises(ValidationError):
            Validator.validate_text("")
    
    def test_validate_text_too_long(self):
        """Test text length limit."""
        long_text = "x" * 11000
        with pytest.raises(ValidationError):
            Validator.validate_text(long_text)
    
    def test_validate_text_whitespace_only(self):
        """Test whitespace-only text."""
        with pytest.raises(ValidationError):
            Validator.validate_text("   \t\n   ")
    
    def test_validate_query_valid(self):
        """Test valid query validation."""
        query = "search for documents"
        result = Validator.validate_query(query)
        assert result == query
    
    def test_validate_query_sql_injection(self):
        """Test SQL injection detection."""
        with pytest.raises(ValidationError):
            Validator.validate_query("test' UNION SELECT * FROM users--")
    
    def test_validate_query_xss(self):
        """Test XSS injection detection."""
        with pytest.raises(ValidationError):
            Validator.validate_query("test<script>alert('xss')</script>")
    
    def test_validate_number_valid(self):
        """Test valid number validation."""
        result = Validator.validate_number(42)
        assert result == 42.0
    
    def test_validate_number_range(self):
        """Test number range validation."""
        with pytest.raises(ValidationError):
            Validator.validate_number(100, min_val=0, max_val=50)
    
    def test_validate_batch_valid(self):
        """Test valid batch validation."""
        docs = ["Doc 1", "Doc 2", "Doc 3"]
        result = Validator.validate_batch(docs)
        assert len(result) == 3
    
    def test_validate_batch_too_large(self):
        """Test batch size limit."""
        docs = ["Doc " + str(i) for i in range(1100)]
        with pytest.raises(ValidationError):
            Validator.validate_batch(docs, max_size=1000)
    
    def test_validate_batch_empty(self):
        """Test empty batch validation."""
        with pytest.raises(ValidationError):
            Validator.validate_batch([])
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        text = "<script>alert('xss')</script>Hello"
        sanitized = Validator.sanitize_text(text)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
    
    def test_validate_email_valid(self):
        """Test valid email validation."""
        result = Validator.validate_email("user@example.com")
        assert result == "user@example.com"
    
    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        with pytest.raises(ValidationError):
            Validator.validate_email("invalid-email")


# ==================== Circuit Breaker Tests ====================

class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    def test_circuit_closed_state(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker("test")
        assert breaker.get_state() == "closed"
        
        def success_fn():
            return "success"
        
        result = breaker.call(success_fn)
        assert result == "success"
    
    def test_circuit_opens_on_failures(self):
        """Test circuit opens when failure rate exceeds threshold."""
        breaker = CircuitBreaker("test", failure_threshold=0.3)
        
        def failing_fn():
            raise Exception("Service error")
        
        # Cause failures
        for i in range(10):
            try:
                breaker.call(failing_fn)
            except Exception:
                pass
        
        # Circuit should open
        assert breaker.get_state() == "open"
    
    def test_circuit_open_rejects_calls(self):
        """Test open circuit rejects new calls."""
        breaker = CircuitBreaker("test", failure_threshold=0.5, recovery_timeout=0)
        
        def failing_fn():
            raise Exception("Error")
        
        # Open circuit
        for i in range(10):
            try:
                breaker.call(failing_fn)
            except:
                pass
        
        assert breaker.get_state() == "open"
        
        # New calls should be rejected
        def good_fn():
            return "ok"
        
        with pytest.raises(CircuitBreakerError):
            breaker.call(good_fn)
    
    def test_circuit_recovery(self):
        """Test circuit breaker recovery."""
        breaker = CircuitBreaker("test", failure_threshold=0.5, recovery_timeout=0)
        
        # Cause failures to open circuit
        def failing_fn():
            raise Exception("Error")
        
        for i in range(10):
            try:
                breaker.call(failing_fn)
            except:
                pass
        
        assert breaker.get_state() == "open"
        
        # Wait for recovery timeout (0 in this test)
        time.sleep(0.1)
        
        # Call should succeed and move to half-open then closed
        def success_fn():
            return "ok"
        
        result = breaker.call(success_fn)
        assert result == "ok"
        assert breaker.get_state() == "closed"
    
    def test_circuit_reset(self):
        """Test circuit breaker reset."""
        breaker = CircuitBreaker("test")
        
        def failing_fn():
            raise Exception("Error")
        
        # Cause failures
        for i in range(10):
            try:
                breaker.call(failing_fn)
            except:
                pass
        
        assert breaker.get_state() == "open"
        
        # Reset
        breaker.reset()
        assert breaker.get_state() == "closed"
    
    def test_circuit_stats(self):
        """Test circuit breaker statistics."""
        breaker = CircuitBreaker("test")
        
        stats = breaker.get_stats()
        assert stats['name'] == "test"
        assert stats['state'] == "closed"
        assert stats['failures'] == 0
        assert stats['successes'] == 0


# ==================== Integration Tests ====================

class TestTier1Integration:
    """Integration tests for all Tier 1 components."""
    
    def setup_method(self):
        """Setup for integration tests."""
        reset_cache()
    
    def test_cache_with_validation(self):
        """Test cache and validation together."""
        cache = get_cache()
        
        def analyze_with_validation(text):
            # Validate input
            Validator.validate_text(text)
            return f"Analyzed: {text[:20]}..."
        
        # First call
        result1 = cache.get("analysis:test", 
                           lambda: analyze_with_validation("test text"))
        assert "Analyzed" in result1
        
        # Second call (cached)
        result2 = cache.get("analysis:test", 
                           lambda: analyze_with_validation("test text"))
        assert result1 == result2
        assert cache.hits == 1
    
    def test_circuit_breaker_with_cache(self):
        """Test circuit breaker protecting cached operations."""
        cache = get_cache()
        breaker = CircuitBreaker("api", failure_threshold=0.3)
        
        success_count = 0
        error_count = 0
        
        def fetch_data_with_protection():
            nonlocal success_count, error_count
            def api_call():
                # Simulate consistent API for predictable testing
                nonlocal success_count
                success_count += 1
                return "data"
            
            try:
                return breaker.call(api_call)
            except CircuitBreakerError:
                error_count += 1
                return None
        
        # Run multiple times with protection
        for i in range(5):
            result = cache.get(f"data:{i}", fetch_data_with_protection, ttl=60)
        
        # Check circuit breaker is working
        assert breaker.success_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
