"""
Rate limiting middleware for FastAPI - Prevents abuse and DoS attacks.

Features:
- Per-IP rate limiting
- Per-user rate limiting
- Token bucket algorithm
- Configurable limits
- Automatic cleanup

Usage:
    from src.api.rate_limiter import RateLimiter
    from fastapi import FastAPI
    
    app = FastAPI()
    limiter = RateLimiter()
    
    # Add middleware
    app.add_middleware(limiter.middleware_factory)
    
    # Or use decorator
    @app.get("/api/endpoint")
    @limiter.limit("10/minute")
    async def endpoint():
        return {"status": "ok"}
"""

from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from functools import wraps
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging
import asyncio

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens (capacity)
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = datetime.now()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            True if tokens available, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now


class RateLimiter:
    """Rate limiting with token bucket algorithm."""
    
    def __init__(self, default_limit: str = "100/minute", 
                 cleanup_interval: int = 300):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Default rate limit (e.g., "100/minute")
            cleanup_interval: Seconds between cleanup of expired buckets
        """
        self.default_limit = default_limit
        self.cleanup_interval = cleanup_interval
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = datetime.now()
        self._parse_limit(default_limit)
    
    def _parse_limit(self, limit_str: str) -> Tuple[int, float]:
        """
        Parse limit string like '100/minute'.
        
        Args:
            limit_str: Limit string
        
        Returns:
            (capacity, refill_rate) tuple
        """
        parts = limit_str.split('/')
        count = int(parts[0])
        
        period = parts[1] if len(parts) > 1 else "minute"
        
        periods = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }
        
        period_seconds = periods.get(period, 60)
        refill_rate = count / period_seconds
        
        return count, refill_rate
    
    def _get_bucket(self, key: str, limit: Optional[str] = None) -> TokenBucket:
        """Get or create token bucket for key."""
        if key not in self.buckets:
            capacity, refill_rate = self._parse_limit(limit or self.default_limit)
            self.buckets[key] = TokenBucket(capacity, refill_rate)
            logger.debug(f"Created rate limit bucket: {key} ({capacity}/{refill_rate:.2f}s)")
        
        return self.buckets[key]
    
    def _cleanup_expired_buckets(self) -> None:
        """Remove unused buckets to prevent memory leak."""
        now = datetime.now()
        if (now - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return
        
        # Remove buckets not used in 30 minutes
        expired_keys = []
        for key, bucket in self.buckets.items():
            age = (now - bucket.last_refill).total_seconds()
            if age > 1800:  # 30 minutes
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.buckets[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit buckets")
        
        self.last_cleanup = now
    
    def is_allowed(self, key: str, limit: Optional[str] = None) -> bool:
        """
        Check if request is allowed.
        
        Args:
            key: Rate limit key (e.g., IP address, user ID)
            limit: Rate limit string (e.g., "100/minute")
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        bucket = self._get_bucket(key, limit)
        allowed = bucket.consume(1)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for: {key}")
        
        self._cleanup_expired_buckets()
        
        return allowed
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        bucket = self.buckets.get(key)
        if bucket is None:
            capacity, _ = self._parse_limit(self.default_limit)
            return capacity
        return int(bucket.tokens)
    
    async def middleware_factory(self, request: Request, call_next):
        """
        FastAPI middleware factory.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self.is_allowed(client_ip):
            remaining = self.get_remaining(client_ip)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "remaining": remaining
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Remaining": str(remaining)
                }
            )
        
        # Call next middleware/handler
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.get_remaining(client_ip)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def limit(self, limit_str: str = "100/minute"):
        """
        Decorator for limiting endpoint.
        
        Usage:
            @app.get("/endpoint")
            @limiter.limit("10/minute")
            async def endpoint():
                return {"status": "ok"}
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                client_ip = request.client.host if request.client else "unknown"
                
                if not self.is_allowed(client_ip, limit_str):
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Rate limit exceeded"}
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            'active_buckets': len(self.buckets),
            'default_limit': self.default_limit,
            'cleanup_interval': self.cleanup_interval,
            'last_cleanup': self.last_cleanup.isoformat()
        }
