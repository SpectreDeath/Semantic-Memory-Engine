"""
Tests for gateway/circuit_breaker.py - Circuit Breaker pattern.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import time
from unittest.mock import patch

import pytest

from gateway.circuit_breaker import CircuitBreaker, CircuitState, get_sidecar_circuit_breaker


class DummyError(Exception):
    pass


def test_initial_state():
    cb = CircuitBreaker(name="test")
    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 0


def test_success_call():
    cb = CircuitBreaker(name="test")
    calls = []

    def func():
        calls.append(1)
        return "ok"

    result = cb.call(func)
    assert result == "ok"
    assert len(calls) == 1
    assert cb.state == CircuitState.CLOSED


def test_failure_threshold_opens_circuit():
    cb = CircuitBreaker(name="test", failure_threshold=3)
    func = lambda: (_ for _ in ()).throw(DummyError("fail"))

    # Call until threshold
    for _ in range(3):
        cb.call(func, fallback="fallback")

    assert cb.state == CircuitState.OPEN
    # Subsequent call should return fallback without invoking func
    call_count = 0

    def func2():
        nonlocal call_count
        call_count += 1
        return "should not run"

    result = cb.call(func2, fallback="fallback")
    assert result == "fallback"
    assert call_count == 0


def test_half_open_after_timeout(monkeypatch):
    cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=1.0)
    func = lambda: (_ for _ in ()).throw(DummyError("fail"))

    # Open the circuit
    cb.call(func, fallback="fb")
    cb.call(func, fallback="fb")
    assert cb.state == CircuitState.OPEN

    # Move time forward beyond recovery_timeout
    base_time = time.time()
    monkeypatch.setattr(time, "time", lambda: base_time + 2)
    # Accessing state property triggers transition
    state = cb.state
    assert state == CircuitState.HALF_OPEN


def test_half_open_success_closes_circuit(monkeypatch):
    cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.1, success_threshold=2)
    fail_func = lambda: (_ for _ in ()).throw(DummyError("fail"))
    success_func = lambda: "ok"

    # Open circuit
    for _ in range(2):
        cb.call(fail_func, fallback="fb")
    assert cb.state == CircuitState.OPEN

    # Fast forward time
    base_time = time.time()
    monkeypatch.setattr(time, "time", lambda: base_time + 1)
    # Trigger half-open
    _ = cb.state
    assert cb.state == CircuitState.HALF_OPEN

    # Successful calls should close circuit
    for _ in range(2):
        result = cb.call(success_func)
        assert result == "ok"

    assert cb.state == CircuitState.CLOSED


def test_half_open_failure_reopens(monkeypatch):
    cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0.1, success_threshold=2)
    fail_func = lambda: (_ for _ in ()).throw(DummyError("fail"))

    # Open
    for _ in range(2):
        cb.call(fail_func, fallback="fb")
    # Fast forward to half-open
    base_time = time.time()
    monkeypatch.setattr(time, "time", lambda: base_time + 1)
    _ = cb.state  # triggers HALF_OPEN

    # One failure should revert to OPEN
    cb.call(fail_func, fallback="fb")
    assert cb.state == CircuitState.OPEN


def test_excluded_exceptions_not_counted():
    cb = CircuitBreaker(name="test", failure_threshold=2, excluded_exceptions=(ValueError,))

    def raise_value():
        raise ValueError("excluded")

    # Two excluded exceptions should not increase failure count
    cb.call(raise_value, fallback="fb")
    cb.call(raise_value, fallback="fb")
    assert cb.state == CircuitState.CLOSED


def test_reset():
    cb = CircuitBreaker(name="test", failure_threshold=2)
    fail_func = lambda: (_ for _ in ()).throw(DummyError("fail"))
    for _ in range(2):
        cb.call(fail_func, fallback="fb")
    assert cb.state == CircuitState.OPEN
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 0
    assert cb._success_count == 0


def test_get_sidecar_circuit_breaker_singleton():
    a = get_sidecar_circuit_breaker()
    b = get_sidecar_circuit_breaker()
    assert a is b
    # Check default configuration
    assert a.name == "sidecar"
    assert a.failure_threshold == 5
    assert a.recovery_timeout == 30.0
    assert a.success_threshold == 3
