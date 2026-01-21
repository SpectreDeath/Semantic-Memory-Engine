"""
Advanced resilience patterns for fault tolerance and graceful degradation.

Implements circuit breaker, retry logic with exponential backoff, timeout policies,
and bulkhead isolation to prevent cascade failures.

Features:
- Circuit breaker pattern (open/closed/half-open states)
- Exponential backoff with jitter for retries
- Request timeout enforcement
- Bulkhead isolation for concurrency limits
- Metrics and monitoring

Usage:
    from src.core.resilience import CircuitBreaker, retry_with_backoff
    
    # Circuit breaker
    breaker = CircuitBreaker("database", failure_threshold=0.5)
    
    @breaker
    def call_database():
        return db.query()
    
    # Retry decorator
    @retry_with_backoff(max_attempts=3, base_delay=1)
    def risky_operation():
        return compute_result()
"""

from typing import Callable, Any, Optional, Dict, TypeVar
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps
import logging
import time
import random
from threading import Lock

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject requests
    HALF_OPEN = "half_open"    # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for resilient error handling.
    
    Prevents cascade failures by monitoring failure rates and opening
    the circuit when they exceed thresholds.
    """
    
    def __init__(self, name: str, failure_threshold: float = 0.5,
                 recovery_timeout: int = 60, expected_exception: type = Exception):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit name (for logging)
            failure_threshold: Failure rate to open circuit (0.0-1.0)
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function raises expected exception
        """
        self._check_state()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _check_state(self) -> None:
        """Check if we should change state."""
        if self.state == CircuitState.CLOSED:
            return
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
            if time_since_failure > self.recovery_timeout:
                logger.info(
                    f"Circuit '{self.name}' OPEN → HALF_OPEN "
                    f"(timeout {self.recovery_timeout}s elapsed)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.failure_count = 0
                self.last_state_change = datetime.now()
            else:
                remaining = self.recovery_timeout - int(time_since_failure)
                raise CircuitBreakerError(
                    f"Circuit '{self.name}' is OPEN. "
                    f"Recovery in {remaining}s")
        
        elif self.state == CircuitState.HALF_OPEN:
            # In half-open, try limited requests
            if self.failure_count > 0:
                # Failed during recovery
                logger.error(
                    f"Circuit '{self.name}' HALF_OPEN → OPEN "
                    f"(recovery failed)")
                self.state = CircuitState.OPEN
                self.last_failure_time = datetime.now()
                raise CircuitBreakerError(
                    f"Circuit '{self.name}' re-opened after recovery attempt")
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Successful recovery
            logger.info(f"Circuit '{self.name}' HALF_OPEN → CLOSED (recovered)")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_state_change = datetime.now()
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        total = self.failure_count + self.success_count
        if total > 0:
            failure_rate = self.failure_count / total
            
            if failure_rate >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.error(
                        f"Circuit '{self.name}' CLOSED → OPEN "
                        f"(failure rate: {failure_rate:.2%})")
                    self.state = CircuitState.OPEN
                    self.last_state_change = datetime.now()
    
    def get_state(self) -> str:
        """Get current circuit state."""
        return self.state.value
    
    def reset(self) -> None:
        """Reset circuit to closed state."""
        old_state = self.state.value
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit '{self.name}' reset ({old_state} → CLOSED)")
    
    def get_stats(self) -> dict:
        """Get circuit statistics."""
        total = self.failure_count + self.success_count
        failure_rate = (self.failure_count / total * 100) if total > 0 else 0
        
        time_in_state = (datetime.now() - self.last_state_change).total_seconds()
        
        return {
            'name': self.name,
            'state': self.state.value,
            'failures': self.failure_count,
            'successes': self.success_count,
            'total': total,
            'failure_rate_percent': f"{failure_rate:.1f}%",
            'time_in_state_seconds': int(time_in_state),
            'last_state_change': self.last_state_change.isoformat(),
            'last_failure': (self.last_failure_time.isoformat() 
                           if self.last_failure_time else None)
        }
    def __call__(self, func: F) -> F:
        """Use circuit breaker as decorator."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper


# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 300.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable:
    """
    Decorator for retrying with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to delay
        on_retry: Callback on retry (attempt_num, exception)
    
    Usage:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def unreliable_operation():
            return result
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        # Calculate delay with exponential backoff
                        delay = base_delay * (exponential_base ** (attempt - 1))
                        delay = min(delay, max_delay)
                        
                        # Add jitter
                        if jitter:
                            delay *= (0.5 + random.random())
                        
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        # Call retry callback
                        if on_retry:
                            on_retry(attempt, e)
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            
            # All attempts failed
            raise last_exception

        return wrapper

    return decorator


# ============================================================================
# Timeout Management
# ============================================================================


class TimeoutError(Exception):
    """Raised when operation times out."""
    pass


class TimeoutManager:
    """Manages operation timeouts."""

    def __init__(self, timeout_seconds: float):
        """Initialize timeout manager."""
        self.timeout_seconds = timeout_seconds
        self.start_time: Optional[float] = None
        self.lock = Lock()

    def __enter__(self):
        """Context manager entry."""
        with self.lock:
            self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        with self.lock:
            self.start_time = None

    def check_timeout(self) -> None:
        """Check if timeout exceeded."""
        with self.lock:
            if self.start_time is None:
                return
            
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(
                    f"Operation timeout: {elapsed:.2f}s > {self.timeout_seconds}s"
                )

    def remaining(self) -> float:
        """Get remaining time in seconds."""
        with self.lock:
            if self.start_time is None:
                return self.timeout_seconds
            
            elapsed = time.time() - self.start_time
            return max(0, self.timeout_seconds - elapsed)


# ============================================================================
# Bulkhead Isolation
# ============================================================================


class BulkheadIsolation:
    """
    Bulkhead isolation pattern.
    
    Limits concurrent requests to prevent resource exhaustion.
    """

    def __init__(self, max_concurrent: int = 10, name: Optional[str] = None):
        """Initialize bulkhead isolation."""
        self.max_concurrent = max_concurrent
        self.name = name or "Bulkhead"
        self.active_count = 0
        self.lock = Lock()

    def acquire(self) -> bool:
        """Try to acquire a permit."""
        with self.lock:
            if self.active_count < self.max_concurrent:
                self.active_count += 1
                return True
            return False

    def release(self) -> None:
        """Release a permit."""
        with self.lock:
            if self.active_count > 0:
                self.active_count -= 1

    def __call__(self, func: F) -> F:
        """Use as decorator."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not self.acquire():
                raise RuntimeError(
                    f"{self.name} bulkhead full ({self.active_count}/{self.max_concurrent})"
                )
            
            try:
                return func(*args, **kwargs)
            finally:
                self.release()

        return wrapper

    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics."""
        with self.lock:
            return {
                "name": self.name,
                "max_concurrent": self.max_concurrent,
                "active_count": self.active_count,
                "available": self.max_concurrent - self.active_count,
            }


# ============================================================================
# Resilient Executor
# ============================================================================


class ResilientExecutor:
    """
    High-level executor combining multiple resilience patterns.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        timeout_seconds: float = 30.0,
        bulkhead: Optional[BulkheadIsolation] = None,
        max_retries: int = 3,
    ):
        """Initialize resilient executor."""
        self.circuit_breaker = circuit_breaker or CircuitBreaker("default")
        self.timeout_seconds = timeout_seconds
        self.bulkhead = bulkhead or BulkheadIsolation()
        self.max_retries = max_retries

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with full resilience."""
        
        @retry_with_backoff(max_attempts=self.max_retries)
        def retry_wrapper():
            # Check bulkhead
            if not self.bulkhead.acquire():
                raise RuntimeError("Bulkhead full")
            
            try:
                # Apply timeout
                with TimeoutManager(self.timeout_seconds) as tm:
                    tm.check_timeout()
                    # Apply circuit breaker
                    return self.circuit_breaker.call(func, *args, **kwargs)
            finally:
                self.bulkhead.release()

        return retry_wrapper()

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "circuit_breaker": self.circuit_breaker.get_stats(),
            "bulkhead": self.bulkhead.get_stats(),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }


# ============================================================================
# Singleton Executor
# ============================================================================

_resilient_executor: Optional[ResilientExecutor] = None
_executor_lock = Lock()


def get_resilient_executor() -> ResilientExecutor:
    """Get or create resilient executor singleton."""
    global _resilient_executor
    if _resilient_executor is None:
        with _executor_lock:
            if _resilient_executor is None:
                _resilient_executor = ResilientExecutor()
    return _resilient_executor


def reset_resilience():
    """Reset resilience patterns (for testing)."""
    global _resilient_executor
    _resilient_executor = None