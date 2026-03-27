"""
Python Version Compatibility Tests for Operator (3.14) and Sidecar (3.13)

Tests ensure compatibility between the operator running Python 3.14 and
the sidecar running Python 3.13.

Run with:
    pytest tests/test_python_version.py -v -m integration
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPythonVersionImports:
    """Test that imports work correctly on Python 3.14."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up required environment variables for all tests in this class."""
        original_env = os.environ.copy()
        os.environ.setdefault("SME_GATEWAY_SECRET", "test_secret_for_imports")
        yield
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.mark.integration
    def test_operator_imports(self):
        """Test that all main operator modules can be imported."""
        import importlib

        modules_to_test = [
            "gateway.auth",
            "gateway.circuit_breaker",
            "src.core.env_validator",
        ]

        for module_name in modules_to_test:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    @pytest.mark.integration
    def test_secrets_module_available(self):
        """Test that secrets module with compare_digest is available."""
        import secrets

        assert hasattr(secrets, "compare_digest"), "secrets.compare_digest not available"
        assert callable(secrets.compare_digest), "secrets.compare_digest is not callable"

    @pytest.mark.integration
    def test_import_compatibility_with_sidecar(self):
        """Test that code patterns used are compatible with Python 3.13."""
        import sys

        assert sys.version_info >= (3, 13), "Tests should run on Python 3.13+"

        python_version = sys.version_info
        major, minor = python_version.major, python_version.minor
        assert major == 3 and minor >= 13, f"Expected Python 3.13+, got {major}.{minor}"


class TestCircuitBreaker:
    """Test circuit breaker functionality for sidecar communication."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a fresh circuit breaker instance for testing."""
        from gateway.circuit_breaker import CircuitBreaker

        return CircuitBreaker(
            name="test_sidecar",
            failure_threshold=3,
            recovery_timeout=1.0,
            success_threshold=2,
        )

    @pytest.mark.integration
    def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker starts in closed state."""
        from gateway.circuit_breaker import CircuitState

        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.integration
    def test_circuit_breaker_normal_operation(self, circuit_breaker):
        """Test circuit breaker allows successful calls."""

        def successful_call():
            return "success"

        result = circuit_breaker.call(successful_call)
        assert result == "success"

    @pytest.mark.integration
    def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures."""
        from gateway.circuit_breaker import CircuitState

        def failing_call():
            raise ValueError("Simulated failure")

        for _ in range(3):
            circuit_breaker.call(failing_call)

        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.integration
    def test_circuit_breaker_returns_fallback_when_open(self, circuit_breaker):
        """Test circuit breaker returns fallback when open."""

        def failing_call():
            raise ValueError("Simulated failure")

        for _ in range(3):
            circuit_breaker.call(failing_call)

        result = circuit_breaker.call(lambda: "should not reach", fallback="fallback_value")
        assert result == "fallback_value"

    @pytest.mark.integration
    def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker can recover from open state."""
        from gateway.circuit_breaker import CircuitState

        for _ in range(3):
            circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert circuit_breaker.state == CircuitState.OPEN

        time.sleep(1.5)

        assert circuit_breaker.state == CircuitState.HALF_OPEN

        for _ in range(2):
            circuit_breaker.call(lambda: "success")

        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.integration
    def test_circuit_breaker_manual_reset(self, circuit_breaker):
        """Test circuit breaker can be manually reset."""
        from gateway.circuit_breaker import CircuitState

        for _ in range(3):
            circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert circuit_breaker.state == CircuitState.OPEN

        circuit_breaker.reset()

        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.integration
    def test_sidecar_circuit_breaker_singleton(self):
        """Test that get_sidecar_circuit_breaker returns singleton."""
        from gateway.circuit_breaker import get_sidecar_circuit_breaker

        cb1 = get_sidecar_circuit_breaker()
        cb2 = get_sidecar_circuit_breaker()

        assert cb1 is cb2, "get_sidecar_circuit_breaker should return singleton"


class TestAuthModule:
    """Test authentication module with constant-time comparison."""

    @pytest.fixture
    def auth_manager(self):
        """Create auth manager with test credentials."""

        env_vars = {
            "SME_GATEWAY_SECRET": "test_secret_key_for_testing_12345",
            "SME_ADMIN_PASSWORD": "test_admin_password",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            import importlib

            import gateway.auth as auth_module
            from gateway.auth import AuthManager

            importlib.reload(auth_module)
            return AuthManager(admin_password="test_admin_password")

    @pytest.mark.integration
    def test_login_correct_password(self, auth_manager):
        """Test successful login with correct password."""
        token = auth_manager.login("admin", "test_admin_password")
        assert token is not None, "Login should return a token"
        assert isinstance(token, str), "Token should be a string"

    @pytest.mark.integration
    def test_login_wrong_password(self, auth_manager):
        """Test login fails with wrong password."""
        token = auth_manager.login("admin", "wrong_password")
        assert token is None, "Login should fail with wrong password"

    @pytest.mark.integration
    def test_constant_time_comparison(self):
        """Test that compare_digest provides constant-time comparison."""
        import secrets

        result1 = secrets.compare_digest("test_password", "test_password")
        assert result1 is True, "Same strings should match"

        result2 = secrets.compare_digest("test_password", "wrong_password")
        assert result2 is False, "Different strings should not match"

        result3 = secrets.compare_digest("abc", "abc")
        assert result3 is True

        result4 = secrets.compare_digest("abc", "xyz")
        assert result4 is False

    @pytest.mark.integration
    def test_token_verification(self, auth_manager):
        """Test JWT token verification."""
        token = auth_manager.login("admin", "test_admin_password")
        assert token is not None

        payload = auth_manager.verify_token(token)
        assert payload is not None, "Token should verify successfully"
        assert payload.get("sub") == "admin"
        assert payload.get("role") == "admin"

    @pytest.mark.integration
    def test_invalid_token_verification(self, auth_manager):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.string"
        result = auth_manager.verify_token(invalid_token)
        assert result is None, "Invalid token should return None"


class TestEnvironmentValidator:
    """Test environment variable validation."""

    @pytest.fixture
    def clean_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.fixture
    def validator(self):
        """Create environment validator."""
        from src.core.env_validator import EnvValidator

        return EnvValidator()

    @pytest.mark.integration
    def test_validate_non_empty_string_valid(self, validator):
        """Test validation of valid non-empty string."""
        from src.core.env_validator import validate_non_empty_string

        result = validate_non_empty_string("valid_value")
        assert result == "valid_value"

    @pytest.mark.integration
    def test_validate_non_empty_string_empty(self, validator):
        """Test validation of empty string."""
        from src.core.env_validator import validate_non_empty_string

        result = validate_non_empty_string("")
        assert result is None

    @pytest.mark.integration
    def test_validate_non_empty_string_none(self, validator):
        """Test validation of None."""
        from src.core.env_validator import validate_non_empty_string

        result = validate_non_empty_string(None)
        assert result is None

    @pytest.mark.integration
    def test_validate_port_valid(self, validator):
        """Test validation of valid port."""
        from src.core.env_validator import validate_port

        result = validate_port("8080")
        assert result == 8080

    @pytest.mark.integration
    def test_validate_port_invalid(self, validator):
        """Test validation of invalid port."""
        from src.core.env_validator import validate_port

        assert validate_port("0") is None
        assert validate_port("70000") is None
        assert validate_port("invalid") is None

    @pytest.mark.integration
    def test_validate_url_valid(self, validator):
        """Test validation of valid URL."""
        from src.core.env_validator import validate_url

        result = validate_url("http://localhost:8080")
        assert result == "http://localhost:8080"

        result = validate_url("https://example.com/path")
        assert result == "https://example.com/path"

    @pytest.mark.integration
    def test_validate_url_invalid(self, validator):
        """Test validation of invalid URL."""
        from src.core.env_validator import validate_url

        assert validate_url("") is None
        assert validate_url("not_a_url") is None

    @pytest.mark.integration
    def test_validate_boolean_valid(self, validator):
        """Test validation of valid boolean."""
        from src.core.env_validator import validate_boolean

        assert validate_boolean("true") is True
        assert validate_boolean("True") is True
        assert validate_boolean("1") is True
        assert validate_boolean("yes") is True
        assert validate_boolean("false") is False
        assert validate_boolean("0") is False

    @pytest.mark.integration
    def test_validate_boolean_invalid(self, validator):
        """Test validation of invalid boolean."""
        from src.core.env_validator import validate_boolean

        assert validate_boolean("") is None
        assert validate_boolean("invalid") is None

    @pytest.mark.integration
    def test_validator_validate_all_required_set(self, validator, clean_env):
        """Test validation with required env vars set."""
        os.environ["SME_GATEWAY_SECRET"] = "test_secret"
        os.environ["SME_ADMIN_PASSWORD"] = "test_password"
        os.environ["SME_HSM_SECRET"] = "test_hsm"

        result = validator.validate_all()

        assert "SME_GATEWAY_SECRET" in result["values"]
        assert "SME_ADMIN_PASSWORD" in result["values"]
        assert len(result["errors"]) == 0, f"Expected no errors, got {result['errors']}"

    @pytest.mark.integration
    def test_validator_validate_all_required_missing(self, validator, clean_env):
        """Test validation with required env vars missing."""
        os.environ.clear()

        result = validator.validate_all()

        assert len(result["errors"]) > 0, "Should have errors for missing required vars"
        assert len(result["warnings"]) > 0, "Should have warnings for optional vars"

    @pytest.mark.integration
    def test_validate_environment_function(self, clean_env):
        """Test the validate_environment function."""
        from src.core.env_validator import validate_environment

        os.environ["SME_GATEWAY_SECRET"] = "test_secret"
        os.environ["SME_ADMIN_PASSWORD"] = "test_password"
        os.environ["SME_HSM_SECRET"] = "test_hsm"

        result = validate_environment()

        assert "values" in result
        assert "errors" in result
        assert "warnings" in result

    @pytest.mark.integration
    def test_env_validator_get_spec(self, validator):
        """Test getting spec for a variable."""
        spec = validator.get_spec("SME_GATEWAY_SECRET")

        assert spec is not None
        assert spec[0] == "SME_GATEWAY_SECRET"
        assert spec[1] is True


class TestCrossVersionCompatibility:
    """Test compatibility patterns between Python 3.13 and 3.14."""

    @pytest.mark.integration
    def test_patterns_compatible_both_versions(self):
        """Test that used patterns work on both Python 3.13 and 3.14."""
        import secrets
        import sys
        import threading

        assert hasattr(secrets, "compare_digest")
        assert hasattr(sys, "version_info")
        assert hasattr(threading, "Lock")

    @pytest.mark.integration
    def test_type_annotations_compatible(self):
        """Test that type annotations are compatible."""
        from typing import Any

        test: str | None = None
        assert test is None

        test = "value"
        assert test == "value"

        test = "value"
        result: Any = test
        assert result == "value"

    @pytest.mark.integration
    def test_f_strings_work(self):
        """Test f-strings work (available in both versions)."""
        value = "test"
        result = f"Value is: {value}"
        assert result == "Value is: test"

    @pytest.mark.integration
    def test_pattern_matching_available(self):
        """Test pattern matching is available (Python 3.10+)."""

        def match_status(code: int) -> str:
            match code:
                case 200:
                    return "OK"
                case 404:
                    return "Not Found"
                case _:
                    return "Unknown"

        assert match_status(200) == "OK"
        assert match_status(404) == "Not Found"
        assert match_status(500) == "Unknown"
