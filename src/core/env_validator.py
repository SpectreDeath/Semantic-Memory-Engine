import os
import logging
from typing import Any, Callable, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EnvValidationError(Exception):
    """Raised when environment validation fails for critical variables."""

    pass


def validate_non_empty_string(value: Optional[str]) -> Optional[str]:
    """Validate that a string is non-empty."""
    if value is None or value == "":
        return None
    return value


def validate_port(value: Optional[str]) -> Optional[int]:
    """Validate that a value is a valid port number (1-65535)."""
    if value is None or value == "":
        return None
    try:
        port = int(value)
        if 1 <= port <= 65535:
            return port
        return None
    except ValueError:
        return None


def validate_url(value: Optional[str]) -> Optional[str]:
    """Validate that a value is a valid URL."""
    if value is None or value == "":
        return None
    try:
        result = urlparse(value)
        if result.scheme and result.netloc:
            return value
        return None
    except Exception:
        return None


def validate_boolean(value: Optional[str]) -> Optional[bool]:
    """Validate that a value is a valid boolean."""
    if value is None or value == "":
        return None
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    return None


EnvVarSpec = tuple[str, bool, Callable[[Optional[str]], Optional[Any]], str]


env_registry: list[EnvVarSpec] = [
    ("SME_GATEWAY_SECRET", True, validate_non_empty_string, "Required gateway secret"),
    ("SME_ADMIN_PASSWORD", True, validate_non_empty_string, "Required admin password"),
    ("SME_HSM_SECRET", True, validate_non_empty_string, "Required HSM secret"),
    ("POSTGRES_USER", False, validate_non_empty_string, "PostgreSQL username"),
    ("POSTGRES_PASSWORD", False, validate_non_empty_string, "PostgreSQL password"),
    ("POSTGRES_DB", False, validate_non_empty_string, "PostgreSQL database name"),
    ("SME_SIDECAR_URL", False, validate_url, "Sidecar service URL"),
    ("SME_CORS_ORIGINS", False, validate_non_empty_string, "CORS origins"),
    ("SME_DATA_DIR", False, validate_non_empty_string, "Data directory path"),
    ("SME_USE_POSTGRES", False, validate_boolean, "Use PostgreSQL flag"),
]


class EnvValidator:
    """Registry and validation for environment variables."""

    def __init__(self, registry: Optional[list[EnvVarSpec]] = None):
        self._registry = registry or env_registry

    def get_spec(self, name: str) -> Optional[EnvVarSpec]:
        """Get the spec for a named variable."""
        for spec in self._registry:
            if spec[0] == name:
                return spec
        return None

    def validate_all(self) -> dict[str, Any]:
        """
        Validate all registered environment variables.

        Returns:
            dict with 'values', 'errors', and 'warnings' keys
        """
        values: dict[str, Any] = {}
        errors: list[str] = []
        warnings: list[str] = []

        for var_name, required, validator, description in self._registry:
            raw_value = os.environ.get(var_name)
            validated = validator(raw_value)

            if validated is not None:
                values[var_name] = validated
            elif required:
                errors.append(f"Required env var '{var_name}' is missing or invalid: {description}")
            else:
                if raw_value is None:
                    warnings.append(f"Optional env var '{var_name}' is not set: {description}")
                else:
                    warnings.append(
                        f"Optional env var '{var_name}' has invalid value: {description}"
                    )

        return {
            "values": values,
            "errors": errors,
            "warnings": warnings,
        }


env_validator = EnvValidator()


def validate_environment() -> dict[str, Any]:
    """
    Validate all registered environment variables.

    Returns:
        dict with 'values', 'errors', and 'warnings' keys
    """
    result = env_validator.validate_all()

    for error in result["errors"]:
        logger.error(error)

    for warning in result["warnings"]:
        logger.warning(warning)

    return result
