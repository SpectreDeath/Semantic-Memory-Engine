"""
Circuit Breaker pattern implementation for resilient service communication.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from enum import Enum
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger("lawnmower.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 3,
        excluded_exceptions: tuple = (),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit '{self.name}': Transitioning to HALF_OPEN")
            return self._state

    def call(self, func: Callable[..., T], fallback: T | None = None, *args, **kwargs) -> T:
        """Execute func with circuit breaker protection."""
        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning(f"Circuit '{self.name}': OPEN - returning fallback")
            return fallback

        try:
            result = func(*args, **kwargs)
            self._on_success(current_state)
            return result
        except Exception as e:
            self._on_failure(e, current_state)
            return fallback

    def _on_success(self, previous_state: CircuitState):
        with self._lock:
            if previous_state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)
                logger.debug(f"Circuit '{self.name}': Success, failure_count={self._failure_count}")
            elif previous_state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"Circuit '{self.name}': Half-open success, success_count={self._success_count}"
                )
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit '{self.name}': Transitioning to CLOSED")

    def _on_failure(self, exception: Exception, previous_state: CircuitState):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if isinstance(exception, self.excluded_exceptions):
                logger.debug(f"Circuit '{self.name}': Excluded exception ignored: {exception}")
                return

            if previous_state == CircuitState.CLOSED:
                logger.warning(
                    f"Circuit '{self.name}': Failure #{self._failure_count}/{self.failure_threshold}: {exception}"
                )
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(f"Circuit '{self.name}': Transitioning to OPEN")
            elif previous_state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(
                    f"Circuit '{self.name}': Half-open failure, transitioning to OPEN: {exception}"
                )

    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = 0.0
            logger.info(f"Circuit '{self.name}': Manually reset to CLOSED")


# Singleton for sidecar circuit breaker
_circuit_breaker: CircuitBreaker | None = None
_circuit_breaker_lock = threading.Lock()


def get_sidecar_circuit_breaker() -> CircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        with _circuit_breaker_lock:
            if _circuit_breaker is None:
                _circuit_breaker = CircuitBreaker(
                    name="sidecar",
                    failure_threshold=5,
                    recovery_timeout=30.0,
                    success_threshold=3,
                )
    return _circuit_breaker
